"""Device TestBox 虚拟仪器的数据模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, model_validator


def _default_params() -> "DeviceTestBoxRunParams":
    return DeviceTestBoxRunParams(duration_s=None, profile=None)


class DeviceTestBoxState(str, Enum):
    INIT = "INIT"
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    RECOVERING = "RECOVERING"
    OFFLINE = "OFFLINE"


class DeviceTestBoxRunParams(BaseModel):
    duration_s: float | None = Field(None, ge=1, le=300, description="诊断持续时长")
    profile: str | None = Field(None, description="诊断配置名称")


class DeviceTestBoxRunCommand(BaseModel):
    command: Literal["testbox.run_diagnostic"] = "testbox.run_diagnostic"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_s: float | None = Field(None, gt=0)
    params: DeviceTestBoxRunParams = Field(default_factory=_default_params)
    metadata: Dict[str, Any] | None = None


class DeviceTestBoxProgressEvent(BaseModel):
    event: Literal["testbox.diagnostic_progress"] = "testbox.diagnostic_progress"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress: float = Field(..., ge=0, le=1)
    stage: str = Field(..., min_length=1)
    message: str | None = None
    metadata: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_stage(self) -> "DeviceTestBoxProgressEvent":
        if not self.stage.strip():
            raise ValueError("stage must not be blank")
        return self


class DeviceTestBoxDoneEvent(BaseModel):
    event: Literal["testbox.diagnostic_done"] = "testbox.diagnostic_done"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_s: float | None = Field(None, ge=0)
    result: Literal["PASS", "FAIL"] = "PASS"
    summary: str | None = None
    metadata: Dict[str, Any] | None = None


class DeviceTestBoxSensorReading(BaseModel):
    name: str
    value: float
    unit: str | None = None


class DeviceTestBoxSensorSnapshot(BaseModel):
    telemetry: Literal["testbox.sensor_snapshot"] = "testbox.sensor_snapshot"
    corr_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sensors: list[DeviceTestBoxSensorReading] = Field(default_factory=list)
    metadata: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _non_empty_sensors(self) -> "DeviceTestBoxSensorSnapshot":
        if not self.sensors:
            raise ValueError("sensors must not be empty")
        return self


class DeviceTestBoxShadow(BaseModel):
    device_id: str = Field(..., min_length=1)
    state: DeviceTestBoxState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_command: str | None = None
    corr_id: str | None = None
    online: bool | None = None
    health: Literal["OK", "WARN", "ERROR"] | None = None
    metadata: Dict[str, Any] | None = None


__all__ = [
    "DeviceTestBoxState",
    "DeviceTestBoxRunParams",
    "DeviceTestBoxRunCommand",
    "DeviceTestBoxProgressEvent",
    "DeviceTestBoxDoneEvent",
    "DeviceTestBoxSensorReading",
    "DeviceTestBoxSensorSnapshot",
    "DeviceTestBoxShadow",
]
