"""Heartbeat and last-will helpers for the TestBox device."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def configure_last_will(
    client: Any,
    *,
    topic: str,
    payload: dict[str, Any],
    qos: int = 1,
    retain: bool = True,
) -> None:
    """Configure MQTT last-will message for the device."""

    try:
        client.will_set(topic, json.dumps(payload), qos=qos, retain=retain)
        logger.info("Configured MQTT LWT on %s", topic)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to configure MQTT LWT: %s", exc)


@dataclass(slots=True)
class HeartbeatConfig:
    topic: str
    interval: float = 30.0
    payload: dict[str, Any] | None = None
    qos: int = 1
    retain: bool = True


class HeartbeatPublisher:
    """Periodic heartbeat publisher using asyncio."""

    def __init__(
        self,
        *,
        client: Any,
        loop: asyncio.AbstractEventLoop,
        config: HeartbeatConfig,
        payload_factory: Optional[Callable[[], dict[str, Any]]] = None,
    ) -> None:
        self._client = client
        self._loop = loop
        self._config = config
        self._payload_factory = payload_factory
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task is not None:
            return
        self._stopped.clear()
        self._task = self._loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stopped.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:  # pragma: no cover - expected
            pass
        finally:
            self._task = None

    async def _run(self) -> None:
        interval = max(0.1, float(self._config.interval))
        while not self._stopped.is_set():
            payload = self._build_payload()
            try:
                self._client.publish(
                    self._config.topic,
                    json.dumps(payload),
                    qos=self._config.qos,
                    retain=self._config.retain,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Heartbeat publish failed: %s", exc)
            await asyncio.sleep(interval)

    def _build_payload(self) -> dict[str, Any]:
        if self._payload_factory is not None:
            return dict(self._payload_factory())
        if self._config.payload is not None:
            return dict(self._config.payload)
        return {"status": "online"}


__all__ = [
    "HeartbeatConfig",
    "HeartbeatPublisher",
    "configure_last_will",
]
