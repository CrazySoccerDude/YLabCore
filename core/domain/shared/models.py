"""跨设备共享的数据模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field


class ErrorEvent(BaseModel):
    """通用错误事件。"""

    event: Literal["system.error"] = "system.error"
    device_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    corr_id: str | None = None
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: Literal["INFO", "WARN", "ERROR"] | None = None
    details: Mapping[str, Any] | None = None


__all__ = ["ErrorEvent"]
