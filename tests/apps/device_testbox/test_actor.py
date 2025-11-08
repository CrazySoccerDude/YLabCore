"""Integration tests for the Device TestBox actor."""

from __future__ import annotations

import asyncio
from typing import List

import pytest

from apps.device_testbox.actor import create_actor
from apps.device_testbox.queues import TelemetryMessage
from core.domain.device_testbox.models import (
    DeviceTestBoxDoneEvent,
    DeviceTestBoxProgressEvent,
    DeviceTestBoxRunCommand,
    DeviceTestBoxRunParams,
)


@pytest.mark.asyncio
async def test_fake_driver_generates_progress_and_done_events() -> None:
    runtime = create_actor(
        {
            "device_id": "TB-001",
            "driver": {"type": "fake", "seed": 1, "default_duration_s": 10.0},
        }
    )

    worker = asyncio.create_task(runtime.actor.run())
    command = DeviceTestBoxRunCommand(
        corr_id="run-1",
        device_id="TB-001",
        params=DeviceTestBoxRunParams(duration_s=12.0, profile="burn-in"),
    )

    await runtime.command_queue.put_command(command)
    await runtime.command_queue.join()

    events: List[TelemetryMessage] = []
    while True:
        try:
            event = await asyncio.wait_for(runtime.telemetry_queue.get_telemetry(), timeout=0.2)
        except asyncio.TimeoutError:
            break
        events.append(event)
        if isinstance(event, DeviceTestBoxDoneEvent):
            break

    runtime.actor.stop()
    await worker

    progress_events = [evt for evt in events if isinstance(evt, DeviceTestBoxProgressEvent)]
    done_events = [evt for evt in events if isinstance(evt, DeviceTestBoxDoneEvent)]

    assert progress_events, "expected progress telemetry from fake driver"
    assert done_events and done_events[0].result == "PASS"
    assert all(getattr(evt, "device_id", "") == "TB-001" for evt in events)
