"""占位：命令输入端口定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CommandPort(ABC):
    """约束上层如何向领域层发起命令。"""

    @abstractmethod
    def dispatch(self, payload: dict) -> None:
        """派发命令。后续引入模型校验与日志。"""
        raise NotImplementedError
