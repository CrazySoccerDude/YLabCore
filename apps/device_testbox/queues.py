"""占位：TestBox 设备内部 SEDA 队列定义。"""

from __future__ import annotations

import asyncio


class CommandQueue(asyncio.Queue):
    """TODO: 处理诊断命令队列，支持优先级与背压。"""


class TelemetryQueue(asyncio.Queue):
    """TODO: 缓冲诊断进度与传感器遥测。"""
