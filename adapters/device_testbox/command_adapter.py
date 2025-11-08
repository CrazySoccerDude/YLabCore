"""TestBox 命令适配器：订阅 MQTT 命令主题并写入命令队列。"""

from __future__ import annotations

import json
import logging
from asyncio import AbstractEventLoop, create_task
from dataclasses import dataclass
from typing import Any, Optional

MQTTClient = Any  # duck-typed at runtime
MQTTMessage = Any

from apps.device_testbox.queues import CommandQueue
from core.domain.device_testbox.models import DeviceTestBoxRunCommand, DeviceTestBoxRunParams


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CommandTopicLayout:
    """约束 TestBox 命令主题结构。"""

    base_topic: str

    @property
    def run_diagnostic(self) -> str:
        return f"{self.base_topic}/cmd/run_diagnostic"


class MQTTCommandAdapter:
    """负责从 MQTT 命令主题解析并压入命令队列。"""

    def __init__(
        self,
        *,
        client: MQTTClient,
    loop: AbstractEventLoop,
        command_queue: CommandQueue,
        topic_layout: CommandTopicLayout,
    ) -> None:
        self._client = client
        self._loop = loop
        self._command_queue = command_queue
        self._topic_layout = topic_layout
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        subscribe_topic = self._topic_layout.run_diagnostic
        logger.info("MQTT command adapter subscribing %s", subscribe_topic)
        self._client.subscribe(subscribe_topic, qos=1)
        self._client.message_callback_add(subscribe_topic, self._on_message)
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        subscribe_topic = self._topic_layout.run_diagnostic
        try:
            self._client.message_callback_remove(subscribe_topic)
            self._client.unsubscribe(subscribe_topic)
        finally:
            self._started = False

    def _on_message(self, client: MQTTClient, userdata: object, message: MQTTMessage) -> None:
        try:
            data = json.loads(message.payload.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - 记录解析异常
            logger.warning("Invalid JSON on %s: %s", message.topic, exc)
            return

        command = self._parse_command(data)
        if command is None:
            return

        logger.debug("Enqueue command %s", command.corr_id)
        self._enqueue_command(command)

    def _parse_command(self, payload: dict) -> Optional[DeviceTestBoxRunCommand]:
        try:
            return DeviceTestBoxRunCommand.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 - 捕获校验错误
            if "params" not in payload:
                payload["params"] = DeviceTestBoxRunParams().model_dump(exclude_none=True)
                try:
                    return DeviceTestBoxRunCommand.model_validate(payload)
                except Exception:
                    logger.warning("Invalid command payload after fallback: %s", exc)
                    return None
            logger.warning("Invalid command payload: %s", exc)
            return None

    def _enqueue_command(self, command: DeviceTestBoxRunCommand) -> None:
        async def _put() -> None:
            await self._command_queue.put_command(command)

        self._loop.call_soon_threadsafe(lambda: create_task(_put()))


__all__ = [
    "CommandTopicLayout",
    "MQTTCommandAdapter",
]
