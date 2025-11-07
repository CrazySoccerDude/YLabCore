"""Device LCR 系列仪器驱动（真实与虚拟实现）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Mapping

from random import Random

from .driver_base import InstrumentDriver


class DeviceLCRFakeDriver(InstrumentDriver):
    """生成可预测阻抗曲线的虚拟驱动，用于联调。"""

    def __init__(self, *, default_points: int = 21, noise_level: float = 0.02, seed: int = 42) -> None:
        self.default_points = max(2, int(default_points))
        self.noise_level = max(0.0, float(noise_level))
        self._rng = Random(seed)
        self._busy = False
        self._last_started: datetime | None = None
        self._last_sweep: list[dict[str, float]] = []

    def identify(self) -> Mapping[str, Any]:
        return {
            "model": "FAKE-LCR",
            "vendor": "InstruHub",
            "firmware": "sim-1.0",
        }

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        if name != "start_sweep":
            raise ValueError(f"unsupported task: {name}")
        self._start_sweep(dict(params))

    def _start_sweep(self, params: Mapping[str, Any]) -> None:
        if self._busy:
            raise RuntimeError("sweep already in progress")
        f_start = float(params.get("f_start_hz", 1.0))
        f_stop = float(params.get("f_stop_hz", 1e6))
        points = int(params.get("points", self.default_points))
        if f_start <= 0 or f_stop <= 0:
            raise ValueError("frequency must be positive")
        if f_stop <= f_start:
            raise ValueError("f_stop_hz must be greater than f_start_hz")
        if points < 2:
            raise ValueError("points must be >= 2")
        self._busy = True
        self._last_started = datetime.now(timezone.utc)
        self._last_sweep = []
        step = (f_stop - f_start) / (points - 1)
        for idx in range(points):
            freq = f_start + step * idx
            base_mag = self._simulate_impedance(freq)
            base_phase = self._simulate_phase(freq)
            noise_scale = 1.0 + (self._rng.random() - 0.5) * 2.0 * self.noise_level
            self._last_sweep.append(
                {
                    "freq_hz": freq,
                    "impedance_ohm": base_mag * noise_scale,
                    "phase_deg": base_phase * noise_scale,
                }
            )
        self._busy = False

    def abort(self) -> None:
        if self._busy:
            self._busy = False
            self._last_sweep = []

    def is_busy(self) -> bool:
        return self._busy

    def last_started_at(self) -> datetime | None:
        return self._last_started

    def fetch_last_sweep(self) -> List[dict[str, float]]:
        return list(self._last_sweep)

    def _simulate_impedance(self, freq_hz: float) -> float:
        pole = 5e3
        return 1000.0 / (1.0 + freq_hz / pole)

    def _simulate_phase(self, freq_hz: float) -> float:
        pole = 5e3
        return -45.0 * (freq_hz / pole) / (1.0 + freq_hz / pole)


class DeviceLCRADMX2001Driver(InstrumentDriver):
    """真实设备驱动占位，将来结合 transport 与 parser 实现。"""

    def identify(self) -> Mapping[str, Any]:
        raise NotImplementedError

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        raise NotImplementedError

    def abort(self) -> None:
        raise NotImplementedError


__all__ = ["DeviceLCRFakeDriver", "DeviceLCRADMX2001Driver"]
