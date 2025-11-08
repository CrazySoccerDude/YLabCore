"""Entry points for the Device TestBox demo and MQTT service."""

from __future__ import annotations


import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from ..domain.models import DeviceTestBoxRunCommand, DeviceTestBoxRunParams

from .actor import DeviceTestBoxRuntime, create_actor
from .queues import TelemetryMessage
from .hb import HeartbeatConfig, HeartbeatPublisher, configure_last_will

LOGGER = logging.getLogger(__name__)


def _default_base_topic(device_id: str) -> str:
    return f"lab/local/line/device_testbox/{device_id}".rstrip("/")


async def run_async(config: Dict[str, Any] | None = None) -> list[TelemetryMessage]:
    """Execute a single diagnostic run and return telemetry events."""

    runtime = create_actor(config)
    actor_task = asyncio.create_task(runtime.actor.run())
    command = runtime.default_command or DeviceTestBoxRunCommand(
        corr_id="demo",
        device_id=runtime.actor.device_id,
        params=DeviceTestBoxRunParams(),
    )
    await runtime.command_queue.put_command(command)
    await runtime.command_queue.join()
    runtime.actor.stop()
    await actor_task
    events: list[TelemetryMessage] = []
    while not runtime.telemetry_queue.empty():
        events.append(runtime.telemetry_queue.get_nowait())
    return events


def run(config: Dict[str, Any] | None = None, *, dump: bool = True) -> Iterable[TelemetryMessage]:
    """Synchronous helper that prints demo telemetry by default."""

    events = asyncio.run(run_async(config))
    if dump:
        for event in events:
            print(event.model_dump_json())
    return events


async def run_mqtt_async(config: Dict[str, Any] | None = None) -> None:
    """MQTT service mode that keeps the actor alive for command handling."""

    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except ImportError as exc:  # noqa: F401
        raise RuntimeError(
            "paho-mqtt 未安装，无法启动 MQTT 模式。请运行 'uv pip install paho-mqtt' 或启用项目依赖。"
        ) from exc

    from ..drivers.command_adapter import CommandTopicLayout, MQTTCommandAdapter
    from ..drivers.state_adapter import StateShadowPublisher, StateTopicLayout
    from ..drivers.telemetry_adapter import MQTTTelemetryAdapter, TelemetryTopicLayout

    cfg = config.copy() if config else {}
    runtime = create_actor(cfg)
    device_id = cfg.get("device_id", runtime.actor.device_id)

    mqtt_cfg = cfg.get("mqtt", {})
    host = mqtt_cfg.get("host", "localhost")
    port = int(mqtt_cfg.get("port", 1883))
    keepalive = int(mqtt_cfg.get("keepalive", 60))
    username = mqtt_cfg.get("username")
    password = mqtt_cfg.get("password")
    base_topic = mqtt_cfg.get("base_topic", _default_base_topic(device_id)).rstrip("/")
    client_id = mqtt_cfg.get("client_id") or f"ylabcore-testbox-{device_id}"

    client = mqtt.Client(client_id=client_id, clean_session=True)
    if username:
        client.username_pw_set(username, password)

    LOGGER.info("Connecting MQTT broker %s:%s", host, port)
    client.connect(host, port, keepalive)
    client.loop_start()

    loop = asyncio.get_running_loop()
    command_adapter = MQTTCommandAdapter(
        client=client,
        loop=loop,
        command_queue=runtime.command_queue,
        topic_layout=CommandTopicLayout(base_topic=base_topic),
    )
    state_publisher = StateShadowPublisher(
        client=client,
        device_id=device_id,
        topic_layout=StateTopicLayout(base_topic=base_topic),
    )
    telemetry_adapter = MQTTTelemetryAdapter(
        client=client,
        telemetry_queue=runtime.telemetry_queue,
        topic_layout=TelemetryTopicLayout(base_topic=base_topic),
        state_publisher=state_publisher,
    )

    heartbeat_config, heartbeat_will = _build_heartbeat_config(
        device_id=device_id,
        base_topic=base_topic,
        mqtt_cfg=mqtt_cfg,
    )
    heartbeat_publisher: HeartbeatPublisher | None = None

    if heartbeat_config is not None:
        configure_last_will(
            client,
            topic=heartbeat_config.topic,
            payload=heartbeat_will,
            qos=heartbeat_config.qos,
            retain=heartbeat_config.retain,
        )
        heartbeat_publisher = HeartbeatPublisher(
            client=client,
            loop=loop,
            config=heartbeat_config,
            payload_factory=lambda: _heartbeat_payload(device_id, heartbeat_config.payload),
        )
        heartbeat_publisher.start()

    command_adapter.start()
    telemetry_adapter.start()

    actor_task = asyncio.create_task(runtime.actor.run())

    try:
        await asyncio.Future()
    finally:
        LOGGER.info("Shutting down TestBox MQTT service")
        command_adapter.stop()
        await telemetry_adapter.stop()
        if heartbeat_publisher is not None:
            await heartbeat_publisher.stop()
        runtime.actor.stop()
        actor_task.cancel()
        try:
            await actor_task
        except asyncio.CancelledError:
            pass
        client.loop_stop()
        client.disconnect()


def run_mqtt(config: Dict[str, Any] | None = None) -> None:
    try:
        asyncio.run(run_mqtt_async(config))
    except KeyboardInterrupt:
        LOGGER.info("TestBox MQTT service interrupted")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Device TestBox service")
    parser.add_argument(
        "--mode",
        choices=["demo", "mqtt"],
        default="demo",
        help="运行模式：demo 输出一次诊断，mqtt 挂载到 broker",
    )
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "../configs/device_testbox.yaml"),
        help="配置文件路径，默认为模块内 device_testbox.yaml",
    )
    return parser


def _load_config(path: str | None) -> Dict[str, Any] | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as fp:
        content = fp.read()
        try:
            import yaml
        except ImportError:
            print("[ERROR] pyyaml 未安装，请运行 'uv pip install pyyaml'")
            raise
        try:
            cfg = yaml.safe_load(content)
            if not cfg:
                print(f"[ERROR] 配置文件内容为空: {path}")
            return cfg
        except Exception as exc:
            print(f"[ERROR] YAML 解析失败: {exc}\n内容如下:\n{content}")
            fp.seek(0)
            try:
                return json.load(fp)
            except Exception as exc2:
                print(f"[ERROR] JSON 解析也失败: {exc2}\n内容如下:\n{content}")
                raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args()
    cfg = _load_config(args.config)
    # 自动提取 device_testbox 子项
    if cfg and "device_testbox" in cfg:
        cfg = cfg["device_testbox"]
    if args.mode == "mqtt":
        run_mqtt(cfg)
    else:
        run(cfg)


def _build_heartbeat_config(
    *,
    device_id: str,
    base_topic: str,
    mqtt_cfg: Dict[str, Any],
) -> tuple[HeartbeatConfig | None, dict[str, Any]]:
    hb_cfg = mqtt_cfg.get("heartbeat") or {}
    interval = float(hb_cfg.get("interval", 30.0))
    if interval <= 0:
        return None, {}

    topic = hb_cfg.get("topic", f"{base_topic}/hb")
    payload = dict(hb_cfg.get("payload") or {})
    payload.setdefault("device_id", device_id)
    payload.setdefault("status", "online")

    will_payload = dict(hb_cfg.get("will_payload") or {})
    will_payload.setdefault("device_id", device_id)
    will_payload.setdefault("status", "offline")

    config = HeartbeatConfig(
        topic=topic,
        interval=interval,
        payload=payload,
        qos=int(hb_cfg.get("qos", 1)),
        retain=_as_bool(hb_cfg.get("retain", True)),
    )
    return config, will_payload


def _heartbeat_payload(device_id: str, base_payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(base_payload or {})
    payload.setdefault("device_id", device_id)
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    return payload


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return bool(value)
