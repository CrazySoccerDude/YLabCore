"""Tests for the Device TestBox MQTT telemetry adapter."""

from __future__ import annotations

import asyncio
from typing import Any, List, Tuple

import pytest

from apps.devices.testbox.drivers.telemetry_adapter import MQTTTelemetryAdapter, TelemetryTopicLayout
from apps.devices.testbox.apps.queues import TelemetryQueue
from apps.devices.testbox.domain.models import DeviceTestBoxDoneEvent, DeviceTestBoxProgressEvent


class _DummyMQTTClient:
    def __init__(self) -> None:
        self.published: List[Tuple[str, str, int, bool]] = []

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        self.published.append((topic, payload, qos, retain))


class _CapturingStatePublisher:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def handle(self, message: Any) -> None:
        self.messages.append(message)


@pytest.mark.asyncio
async def test_telemetry_adapter_publishes_progress_and_done_events() -> None:
    client = _DummyMQTTClient()
    queue = TelemetryQueue()
    layout = TelemetryTopicLayout(base_topic="lab/test/device_testbox/TB-003")
    state_publisher = _CapturingStatePublisher()
    adapter = MQTTTelemetryAdapter(
        client=client,
        telemetry_queue=queue,
        topic_layout=layout,
        state_publisher=state_publisher,
    )

    adapter.start()

    progress = DeviceTestBoxProgressEvent(
        corr_id="corr-321",
        device_id="TB-003",
        progress=0.5,
        stage="calibration",
        points_completed=5,
        points_total=10,
    )
    done = DeviceTestBoxDoneEvent(
        corr_id="corr-321",
        device_id="TB-003",
        points_total=10,
        duration_s=12.3,
    )

    await queue.put_telemetry(progress)
    await queue.put_telemetry(done)
    await asyncio.wait_for(queue.join(), timeout=0.2)

    await adapter.stop()

    topics = [topic for topic, *_ in client.published]
    assert layout.for_progress() in topics
    assert layout.for_done() in topics
    assert state_publisher.messages[0] == progress
    assert state_publisher.messages[1] == done
