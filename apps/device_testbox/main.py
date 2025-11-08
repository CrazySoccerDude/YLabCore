"""TestBox 设备适配器入口，提供 demo 与 MQTT 模式。"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any, Dict, Iterable

from core.domain.device_testbox.models import DeviceTestBoxRunCommand, DeviceTestBoxRunParams

from .actor import DeviceTestBoxRuntime, create_actor
from .queues import TelemetryMessage

LOGGER = logging.getLogger(__name__)


def _default_base_topic(device_id: str) -> str:
    return f"lab/local/line/device_testbox/{device_id}".rstrip("/")


async def run_async(config: Dict[str, Any] | None = None) -> list[TelemetryMessage]:
    """运行一次 demo 命令并返回所有遥测事件。"""

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
    """同步封装，默认打印 demo 遥测。"""

    events = asyncio.run(run_async(config))
    if dump:
        for event in events:
            print(event.model_dump_json())
    return events


async def run_mqtt_async(config: Dict[str, Any] | None = None) -> None:
    """长期运行的 MQTT 服务模式。"""

    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except ImportError as exc:  # noqa: F401 - 提供更友好的提示
        raise RuntimeError(
            "paho-mqtt 未安装，无法启动 MQTT 模式。请运行 'uv pip install paho-mqtt' 或启用项目依赖。"
        ) from exc

    from adapters.device_testbox.command_adapter import CommandTopicLayout, MQTTCommandAdapter
    from adapters.device_testbox.state_adapter import StateShadowPublisher, StateTopicLayout
    from adapters.device_testbox.telemetry_adapter import MQTTTelemetryAdapter, TelemetryTopicLayout

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

    command_adapter.start()
    telemetry_adapter.start()

    actor_task = asyncio.create_task(runtime.actor.run())

    try:
        await asyncio.Future()
    finally:
        LOGGER.info("Shutting down TestBox MQTT service")
        command_adapter.stop()
        await telemetry_adapter.stop()
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
        help="可选 JSON 配置文件路径",
    )
    return parser


def _load_config(path: str | None) -> Dict[str, Any] | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args()
    cfg = _load_config(args.config)
    if args.mode == "mqtt":
        run_mqtt(cfg)
    else:
        run(cfg)
