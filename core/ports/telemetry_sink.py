"""占位：遥测下行端口定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TelemetrySink(ABC):
    """描述遥测数据如何被消费或持久化。"""

    @abstractmethod
    def emit(self, payload: dict) -> None:
        """输出遥测数据，占位实现。"""
        raise NotImplementedError
