"""占位：设备内部 SEDA 队列定义。"""

from __future__ import annotations

import asyncio


class CommandQueue(asyncio.Queue):
    """TODO: 封装命令队列特定行为。"""


class TelemetryQueue(asyncio.Queue):
    """TODO: 遥测队列，支持批处理。"""
