"""通用设备驱动基类，供各设备微服务复用。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Mapping, Optional


class InstrumentDriver(ABC):
    """高阶设备驱动需实现的核心接口。"""

    @abstractmethod
    def identify(self) -> Mapping[str, Any]:
        """返回设备识别信息，例如型号、固件版本。"""
        raise NotImplementedError

    @abstractmethod
    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        """根据任务名称触发实际操作。"""
        raise NotImplementedError

    @abstractmethod
    def abort(self) -> None:
        """请求驱动终止当前执行。"""
        raise NotImplementedError

    def is_busy(self) -> bool:
        """可选：报告当前是否忙碌，默认认为空闲。"""
        return False

    def last_started_at(self) -> Optional[datetime]:
        """可选：返回最近一次开始执行的时间戳。"""
        return None

    def fetch_progress(self) -> list[dict[str, Any]]:
        """可选：拉取阶段性进度信息。默认无数据。"""
        return []

    def fetch_result(self) -> Optional[dict[str, Any]]:
        """可选：拉取最终诊断结果。默认无结果。"""
        return None


__all__ = ["InstrumentDriver"]
