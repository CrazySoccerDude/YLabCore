"""MQTT telemetry adapter consuming the TestBox telemetry queue."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from ..apps.queues import TelemetryMessage, TelemetryQueue
from ..domain.models import (
    DeviceTestBoxDoneEvent,
    DeviceTestBoxProgressEvent,
    DeviceTestBoxSensorSnapshot,
)
from core.domain.shared.models import ErrorEvent

logger = logging.getLogger(__name__)

MQTTClient = Any


@dataclass(slots=True)
class TelemetryTopicLayout:
    base_topic: str

    def for_progress(self) -> str:
        return f"{self.base_topic}/tele/progress"

    def for_done(self) -> str:
        return f"{self.base_topic}/tele/done"

    def for_snapshot(self) -> str:
        return f"{self.base_topic}/tele/sensor_snapshot"

    def for_error(self) -> str:
        return f"{self.base_topic}/evt/error"


class MQTTTelemetryAdapter:
    """Publish telemetry events to MQTT topics."""

    def __init__(
        self,
        *,
        client: MQTTClient,
        telemetry_queue: TelemetryQueue,
        topic_layout: TelemetryTopicLayout,
        state_publisher: Optional["StateShadowPublisher"] = None,
    ) -> None:
        self._client = client
        self._queue = telemetry_queue
        self._topic_layout = topic_layout
        self._state_publisher = state_publisher
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None:
            return
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            message = await self._queue.get_telemetry()
            try:
                topic = self._resolve_topic(message)
                payload = message.model_dump_json()
                logger.debug("Publish telemetry to %s", topic)
                self._client.publish(topic, payload, qos=1)
                if self._state_publisher is not None:
                    self._state_publisher.handle(message)
            finally:
                self._queue.task_done()

    def _resolve_topic(self, message: TelemetryMessage) -> str:
        if isinstance(message, DeviceTestBoxProgressEvent):
            return self._topic_layout.for_progress()
        if isinstance(message, DeviceTestBoxDoneEvent):
            return self._topic_layout.for_done()
        if isinstance(message, DeviceTestBoxSensorSnapshot):
            return self._topic_layout.for_snapshot()
        if isinstance(message, ErrorEvent):
            return self._topic_layout.for_error()
        raise TypeError(f"Unsupported telemetry message: {type(message)!r}")


from .state_adapter import StateShadowPublisher  # noqa: E402


__all__ = [
    "MQTTTelemetryAdapter",
    "TelemetryTopicLayout",
]
