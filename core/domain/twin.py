"""占位：设备数字孪生与层级状态机定义。"""

from __future__ import annotations


class DeviceStateMachine:
    """TODO: 实现 INIT/IDLE/BUSY/ERROR 等状态与转换。"""

    def __init__(self) -> None:
        self.state = "INIT"

    def on_event(self, event: str) -> None:
        """根据事件更新状态的占位方法。"""
        raise NotImplementedError("待实现状态机逻辑")
