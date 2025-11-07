"""Device LCR 仪器相关的数据模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, model_validator


class DeviceLCRState(str, Enum):
    INIT = "INIT"
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    RECOVERING = "RECOVERING"
    OFFLINE = "OFFLINE"


class DeviceLCRSweepParams(BaseModel):
    f_start_hz: float = Field(..., gt=0, description="起始频率 Hz")
    f_stop_hz: float = Field(..., gt=0, description="截止频率 Hz，需大于起始值")
    points: int = Field(..., ge=2, le=16384, description="扫频点数")
    excitation_voltage_v: float | None = Field(None, ge=0, le=20, description="激励电压")
    averaging: int | None = Field(None, ge=1, le=256, description="平均次数")
    settle_time_s: float | None = Field(None, ge=0, description="启动前等待时间")

    @model_validator(mode="after")
    def _validate_range(self) -> "DeviceLCRSweepParams":
        if self.f_stop_hz <= self.f_start_hz:
            raise ValueError("f_stop_hz must be greater than f_start_hz")
        return self


class DeviceLCRStartSweepCommand(BaseModel):
    command: Literal["lcr.start_sweep"] = "lcr.start_sweep"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_s: float | None = Field(None, gt=0)
    idempotency_key: str | None = Field(None, min_length=1)
    params: DeviceLCRSweepParams
    metadata: Dict[str, Any] | None = None


class DeviceLCRSweepProgressEvent(BaseModel):
    event: Literal["lcr.sweep_progress"] = "lcr.sweep_progress"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress: float = Field(..., ge=0, le=1)
    points_completed: int = Field(..., ge=0)
    points_total: int = Field(..., ge=1)
    last_frequency_hz: float | None = Field(None, gt=0)
    metadata: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_points(self) -> "DeviceLCRSweepProgressEvent":
        if self.points_completed > self.points_total:
            raise ValueError("points_completed cannot exceed points_total")
        return self


class DeviceLCRSweepDoneEvent(BaseModel):
    event: Literal["lcr.sweep_done"] = "lcr.sweep_done"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    points_total: int = Field(..., ge=1)
    duration_s: float = Field(..., ge=0)
    metadata: Dict[str, Any] | None = None


class DeviceLCRImpedancePoint(BaseModel):
    telemetry: Literal["lcr.impedance_point"] = "lcr.impedance_point"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freq_hz: float = Field(..., gt=0)
    impedance_ohm: float = Field(..., ge=0)
    phase_deg: float
    excitation_voltage_v: float | None = Field(None, ge=0)
    metadata: Dict[str, Any] | None = None


class DeviceLCRShadow(BaseModel):
    device_id: str = Field(..., min_length=1)
    state: DeviceLCRState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_command: str | None = None
    corr_id: str | None = None
    online: bool | None = None
    health: Literal["OK", "WARN", "ERROR"] | None = None
    metadata: Dict[str, Any] | None = None


__all__ = [
    "DeviceLCRState",
    "DeviceLCRSweepParams",
    "DeviceLCRStartSweepCommand",
    "DeviceLCRSweepProgressEvent",
    "DeviceLCRSweepDoneEvent",
    "DeviceLCRImpedancePoint",
    "DeviceLCRShadow",
]
