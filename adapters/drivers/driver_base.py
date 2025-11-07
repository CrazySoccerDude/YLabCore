"""通用仪器驱动抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class InstrumentDriver(ABC):
    """所有具体仪器驱动需实现的基础接口。"""

    @abstractmethod
    def identify(self) -> Mapping[str, Any]:
        """返回设备识别信息（型号、固件等）。"""
        raise NotImplementedError

    @abstractmethod
    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        """按照任务名称触发具体操作，例如 start_sweep。"""
        raise NotImplementedError

    @abstractmethod
    def abort(self) -> None:
        """请求取消当前操作。"""
        raise NotImplementedError

    def is_busy(self) -> bool:
        """可选实现：返回当前是否忙碌。默认认为非忙碌。"""
        return False
