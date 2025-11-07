"""占位：SCPI 文本协议封装与解析。"""

from __future__ import annotations


def build_command(cmd: str, *args: object) -> str:
    """TODO: 格式化 SCPI 指令。"""
    return cmd


def parse_response(raw: str) -> dict:
    """TODO: 解析 SCPI 响应字符串。"""
    raise NotImplementedError
