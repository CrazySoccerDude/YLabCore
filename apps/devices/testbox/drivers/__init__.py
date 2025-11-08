"""Device TestBox drivers for fake and real backends."""

from __future__ import annotations

from datetime import datetime, timezone
from random import Random
from typing import Any, Dict, List, Mapping

from ...driver_base import InstrumentDriver


class DeviceTestBoxFakeDriver(InstrumentDriver):
    """Virtual diagnostic driver that simulates staged execution."""

    def __init__(
        self,
        *,
        default_duration_s: float = 60.0,
        stages: List[str] | None = None,
        seed: int = 7,
    ) -> None:
        self.default_duration_s = max(1.0, float(default_duration_s))
        self._stages = stages or [
            "power_on_self_test",
            "sensor_calibration",
            "thermal_stabilization",
            "diagnostic_sequence",
            "report_generation",
        ]
        self._rng = Random(seed)
        self._busy = False
        self._last_started: datetime | None = None
        self._last_progress: list[dict[str, Any]] = []
        self._last_result: dict[str, Any] | None = None

    def identify(self) -> Mapping[str, Any]:
        return {
            "model": "FAKE-TESTBOX",
            "vendor": "InstruHub",
            "firmware": "sim-1.0",
        }

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        if name != "run_diagnostic":
            raise ValueError(f"unsupported task: {name}")
        self._run_diagnostic(dict(params))

    def _run_diagnostic(self, params: Dict[str, Any]) -> None:
        if self._busy:
            raise RuntimeError("diagnostic already in progress")
        self._busy = True
        self._last_started = datetime.now(timezone.utc)
        duration = float(params.get("duration_s") or self.default_duration_s)
        profile = params.get("profile") or "default"
        self._last_progress = []
        total = len(self._stages)
        for idx, stage in enumerate(self._stages, start=1):
            jitter = self._rng.uniform(-0.1, 0.1) * duration / total
            elapsed = max(0.0, (duration / total) * idx + jitter)
            self._last_progress.append(
                {
                    "stage": stage,
                    "progress": min(1.0, idx / total),
                    "elapsed_s": round(elapsed, 3),
                    "message": f"{stage} completed",
                }
            )
        self._last_result = {
            "duration_s": round(duration, 3),
            "profile": profile,
            "passed": True,
            "summary": "All diagnostics completed without anomalies.",
        }
        self._busy = False

    def abort(self) -> None:
        if self._busy:
            self._busy = False
            self._last_progress = []
            self._last_result = {
                "duration_s": 0.0,
                "profile": None,
                "passed": False,
                "summary": "Diagnostic aborted by operator.",
            }

    def is_busy(self) -> bool:
        return self._busy

    def last_started_at(self) -> datetime | None:
        return self._last_started

    def fetch_progress(self) -> List[dict[str, Any]]:
        return list(self._last_progress)

    def fetch_result(self) -> dict[str, Any] | None:
        return dict(self._last_result) if self._last_result is not None else None


class DeviceTestBoxRealDriver(InstrumentDriver):
    """Placeholder for the real device driver backed by transport + parser."""

    def identify(self) -> Mapping[str, Any]:
        raise NotImplementedError

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        raise NotImplementedError

    def abort(self) -> None:
        raise NotImplementedError


__all__ = [
    "DeviceTestBoxFakeDriver",
    "DeviceTestBoxRealDriver",
]
