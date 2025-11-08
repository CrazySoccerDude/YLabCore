"""TestBox 设备内部命令与遥测队列实现。"""

from __future__ import annotations

import asyncio
from typing import Union

from core.domain.device_testbox.models import (
    DeviceTestBoxDoneEvent,
    DeviceTestBoxProgressEvent,
    DeviceTestBoxRunCommand,
    DeviceTestBoxSensorSnapshot,
)
from core.domain.shared.models import ErrorEvent

TelemetryMessage = Union[
    DeviceTestBoxProgressEvent,
    DeviceTestBoxDoneEvent,
    DeviceTestBoxSensorSnapshot,
    ErrorEvent,
]


class CommandQueue(asyncio.Queue[DeviceTestBoxRunCommand]):
    """异步命令队列，包装 put/get 便于类型检查。"""

    async def put_command(self, command: DeviceTestBoxRunCommand) -> None:
        await self.put(command)

    async def get_command(self) -> DeviceTestBoxRunCommand:
        command = await self.get()
        return command


class TelemetryQueue(asyncio.Queue[TelemetryMessage]):
    """缓存遥测、进度、错误事件的队列。"""

    async def put_telemetry(self, message: TelemetryMessage) -> None:
        await self.put(message)

    async def get_telemetry(self) -> TelemetryMessage:
        message = await self.get()
        return message


__all__ = [
    "CommandQueue",
    "TelemetryMessage",
    "TelemetryQueue",
]
