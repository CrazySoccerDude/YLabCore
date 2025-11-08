"""TestBox 状态影子适配器：根据遥测事件更新影子。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from apps.device_testbox.queues import TelemetryMessage
from core.domain.device_testbox.models import (
    DeviceTestBoxDoneEvent,
    DeviceTestBoxProgressEvent,
    DeviceTestBoxShadow,
    DeviceTestBoxState,
)
from core.domain.shared.models import ErrorEvent


logger = logging.getLogger(__name__)

MQTTClient = Any


@dataclass(slots=True)
class StateTopicLayout:
    base_topic: str

    def for_shadow(self) -> str:
        return f"{self.base_topic}/state/shadow"


class StateShadowPublisher:
    """基于遥测事件构建并发布设备状态影子。"""

    def __init__(
        self,
        *,
        client: MQTTClient,
        device_id: str,
        topic_layout: StateTopicLayout,
    ) -> None:
        self._client = client
        self._device_id = device_id
        self._topic_layout = topic_layout
        self._shadow = DeviceTestBoxShadow(
            device_id=device_id,
            state=DeviceTestBoxState.IDLE,
        )

    def handle(self, message: TelemetryMessage) -> None:
        updated_shadow: Optional[DeviceTestBoxShadow] = None
        now = datetime.now(timezone.utc)

        if isinstance(message, DeviceTestBoxProgressEvent):
            updated_shadow = self._shadow.model_copy(
                update={
                    "timestamp": now,
                    "state": DeviceTestBoxState.BUSY,
                    "last_command": "testbox.run_diagnostic",
                    "corr_id": message.corr_id,
                    "metadata": {
                        "stage": message.stage,
                        "progress": message.progress,
                    },
                    "health": "OK",
                }
            )
        elif isinstance(message, DeviceTestBoxDoneEvent):
            updated_shadow = self._shadow.model_copy(
                update={
                    "timestamp": now,
                    "state": DeviceTestBoxState.IDLE,
                    "last_command": "testbox.run_diagnostic",
                    "corr_id": message.corr_id,
                    "metadata": {
                        "result": message.result,
                        "duration_s": message.duration_s,
                    },
                    "health": "OK" if message.result == "PASS" else "WARN",
                }
            )
        elif isinstance(message, ErrorEvent):
            updated_shadow = self._shadow.model_copy(
                update={
                    "timestamp": now,
                    "state": DeviceTestBoxState.ERROR,
                    "health": "ERROR",
                    "metadata": {
                        "code": message.code,
                        "severity": message.severity,
                    },
                    "corr_id": message.corr_id,
                }
            )

        if updated_shadow is None:
            return

        self._shadow = updated_shadow
        topic = self._topic_layout.for_shadow()
        payload = self._shadow.model_dump_json()
        logger.debug("Publish state shadow to %s", topic)
        self._client.publish(topic, payload, qos=1, retain=True)


__all__ = [
    "StateShadowPublisher",
    "StateTopicLayout",
]
