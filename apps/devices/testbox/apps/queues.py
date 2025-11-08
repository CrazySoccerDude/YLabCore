"""Command and telemetry queues for the Device TestBox pipeline."""

from __future__ import annotations

import asyncio
from typing import Union

from ..domain.models import (
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
    """Asyncio queue tailored for device commands."""

    async def put_command(self, command: DeviceTestBoxRunCommand) -> None:
        await self.put(command)

    async def get_command(self) -> DeviceTestBoxRunCommand:
        command = await self.get()
        return command


class TelemetryQueue(asyncio.Queue[TelemetryMessage]):
    """Asyncio queue buffering telemetry, progress, and error events."""

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
