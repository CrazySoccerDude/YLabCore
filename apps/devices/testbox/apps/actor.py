"""Device TestBox actor binding command queues to drivers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Iterable

from ..domain.models import (
    DeviceTestBoxDoneEvent,
    DeviceTestBoxProgressEvent,
    DeviceTestBoxRunCommand,
    DeviceTestBoxRunParams,
)
from core.domain.shared.models import ErrorEvent

from ...driver_base import InstrumentDriver

from ..drivers import DeviceTestBoxFakeDriver, DeviceTestBoxRealDriver
from .queues import CommandQueue, TelemetryQueue


class DeviceTestBoxActor:
    """Consume commands and emit telemetry events through the driver."""

    def __init__(
        self,
        *,
        device_id: str,
        driver: InstrumentDriver,
        command_queue: CommandQueue,
        telemetry_queue: TelemetryQueue,
    ) -> None:
        self._device_id = device_id
        self._driver = driver
        self._command_queue = command_queue
        self._telemetry_queue = telemetry_queue
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        """Request the actor loop to exit."""

        self._stop_event.set()

    @property
    def device_id(self) -> str:
        return self._device_id

    async def run(self) -> None:
        """Continuously consume commands and publish telemetry."""

        while True:
            if self._stop_event.is_set() and self._command_queue.empty():
                break
            try:
                command = await asyncio.wait_for(self._command_queue.get_command(), 0.1)
            except asyncio.TimeoutError:
                continue
            try:
                await self._handle_command(command)
            finally:
                self._command_queue.task_done()

    async def _handle_command(self, command: DeviceTestBoxRunCommand) -> None:
        payload = command.params.model_dump(exclude_none=True)
        try:
            self._driver.start_task("run_diagnostic", payload)
            await self._publish_progress(command)
            await self._publish_done(command)
        except Exception as exc:  # noqa: BLE001
            await self._telemetry_queue.put_telemetry(
                ErrorEvent(
                    device_id=command.device_id,
                    corr_id=command.corr_id,
                    code="testbox.actor.error",
                    message=str(exc),
                    severity="ERROR",
                    details={"command": command.model_dump(exclude_none=True)},
                )
            )

    async def _publish_progress(self, command: DeviceTestBoxRunCommand) -> None:
        progress_items = getattr(self._driver, "fetch_progress", None)
        if progress_items is None or not callable(progress_items):
            return
        records: Iterable[Dict[str, Any]] = progress_items()
        for record in records:
            await self._telemetry_queue.put_telemetry(
                DeviceTestBoxProgressEvent(
                    corr_id=command.corr_id,
                    device_id=command.device_id,
                    progress=float(record.get("progress", 0.0)),
                    stage=str(record.get("stage", "unknown")),
                    message=record.get("message"),
                    metadata={
                        "elapsed_s": record.get("elapsed_s"),
                        "device_id": command.device_id,
                    },
                )
            )

    async def _publish_done(self, command: DeviceTestBoxRunCommand) -> None:
        fetch_result = getattr(self._driver, "fetch_result", None)
        if fetch_result is None or not callable(fetch_result):
            return
        result = fetch_result()
        if result is None:
            return
        passed = bool(result.get("passed", False))
        await self._telemetry_queue.put_telemetry(
            DeviceTestBoxDoneEvent(
                corr_id=command.corr_id,
                device_id=command.device_id,
                duration_s=float(result.get("duration_s") or 0.0),
                result="PASS" if passed else "FAIL",
                summary=result.get("summary"),
                metadata={
                    "profile": result.get("profile"),
                    "device_id": command.device_id,
                },
            )
        )


@dataclass(slots=True)
class DeviceTestBoxRuntime:
    actor: DeviceTestBoxActor
    command_queue: CommandQueue
    telemetry_queue: TelemetryQueue
    default_command: DeviceTestBoxRunCommand | None = None


def _build_driver(config: Dict[str, Any]):
    driver_cfg = config.get("driver", {})
    driver_type = driver_cfg.get("type", "fake").lower()
    if driver_type == "fake":
        return DeviceTestBoxFakeDriver(
            default_duration_s=float(driver_cfg.get("default_duration_s", 60.0)),
            stages=list(driver_cfg.get("stages", [])) or None,
            seed=int(driver_cfg.get("seed", 7)),
        )
    if driver_type == "real":
        return DeviceTestBoxRealDriver()
    raise ValueError(f"Unsupported driver type: {driver_type}")


def _resolve_params(config: Dict[str, Any]) -> DeviceTestBoxRunParams:
    params_cfg = config.get("default_params", {})
    if isinstance(params_cfg, DeviceTestBoxRunParams):
        return params_cfg
    return DeviceTestBoxRunParams(**params_cfg)


def create_actor(config: Dict[str, Any] | None = None) -> DeviceTestBoxRuntime:
    """Construct the actor and its queues for the device."""

    cfg = config.copy() if config else {}
    device_id = cfg.get("device_id", "TESTBOX-001")
    command_queue = CommandQueue()
    telemetry_queue = TelemetryQueue()
    driver = _build_driver(cfg)
    actor = DeviceTestBoxActor(
        device_id=device_id,
        driver=driver,
        command_queue=command_queue,
        telemetry_queue=telemetry_queue,
    )

    default_params = _resolve_params(cfg)
    cfg.setdefault(
        "default_command",
        DeviceTestBoxRunCommand(
            corr_id="demo",
            device_id=device_id,
            params=default_params,
        ),
    )
    runtime = DeviceTestBoxRuntime(
        actor=actor,
        command_queue=command_queue,
        telemetry_queue=telemetry_queue,
        default_command=cfg.get("default_command"),
    )
    return runtime


__all__ = [
    "DeviceTestBoxActor",
    "DeviceTestBoxRuntime",
    "create_actor",
]
