"""占位：LCR 仪器驱动基础接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LCRDriver(ABC):
    """定义 LCR 驱动需要实现的方法集合。"""

    @abstractmethod
    def identify(self) -> dict:
        """读取设备标识。"""
        raise NotImplementedError

    @abstractmethod
    def start_sweep(self, params: dict) -> None:
        """开始扫频，参数由 JSON Schema 约束。"""
        raise NotImplementedError

    @abstractmethod
    def abort(self) -> None:
        """取消当前操作。"""
        raise NotImplementedError
