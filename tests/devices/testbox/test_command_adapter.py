"""Tests for the Device TestBox MQTT command adapter."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import pytest

from apps.devices.testbox.drivers.command_adapter import CommandTopicLayout, MQTTCommandAdapter
from apps.devices.testbox.apps.queues import CommandQueue
from apps.devices.testbox.domain.models import DeviceTestBoxRunCommand, DeviceTestBoxRunParams


@dataclass
class _Message:
    topic: str
    payload: bytes


class _DummyMQTTClient:
    def __init__(self) -> None:
        self.subscriptions: list[Tuple[str, int]] = []
        self._callbacks: Dict[str, Callable[[object, object, _Message], None]] = {}
        self.unsubscribed: list[str] = []

    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.subscriptions.append((topic, qos))

    def unsubscribe(self, topic: str) -> None:
        self.unsubscribed.append(topic)

    def message_callback_add(
        self, topic: str, callback: Callable[[object, object, _Message], None]
    ) -> None:
        self._callbacks[topic] = callback

    def message_callback_remove(self, topic: str) -> None:
        self._callbacks.pop(topic, None)

    def emit(self, topic: str, payload: dict) -> None:
        message = _Message(topic=topic, payload=json.dumps(payload).encode("utf-8"))
        cb = self._callbacks[topic]
        cb(self, None, message)


@pytest.mark.asyncio
async def test_command_adapter_enqueues_valid_command() -> None:
    loop = asyncio.get_running_loop()
    queue = CommandQueue()
    client = _DummyMQTTClient()
    layout = CommandTopicLayout(base_topic="lab/test/device_testbox/TB-001")
    adapter = MQTTCommandAdapter(client=client, loop=loop, command_queue=queue, topic_layout=layout)

    adapter.start()
    assert client.subscriptions == [(layout.run_diagnostic, 1)]

    payload = DeviceTestBoxRunCommand(
        corr_id="corr-123",
        device_id="TB-001",
        params=DeviceTestBoxRunParams(duration_s=10.0),
    ).model_dump(mode="json")

    client.emit(layout.run_diagnostic, payload)

    command = await asyncio.wait_for(queue.get_command(), timeout=0.2)
    assert command.command == "testbox.run_diagnostic"
    assert command.corr_id == "corr-123"
    assert command.device_id == "TB-001"

    adapter.stop()
    assert layout.run_diagnostic in client.unsubscribed


@pytest.mark.asyncio
async def test_command_adapter_ignores_invalid_payload() -> None:
    loop = asyncio.get_running_loop()
    queue = CommandQueue()
    client = _DummyMQTTClient()
    layout = CommandTopicLayout(base_topic="lab/test/device_testbox/TB-002")
    adapter = MQTTCommandAdapter(client=client, loop=loop, command_queue=queue, topic_layout=layout)

    adapter.start()

    client.emit(layout.run_diagnostic, {"device_id": "TB-002"})

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(queue.get_command(), timeout=0.1)

    adapter.stop()
