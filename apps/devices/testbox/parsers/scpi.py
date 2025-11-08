"""SCPI 风格指令的格式化与响应解析工具。"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

_SEPARATOR_PATTERN = re.compile(r"[;,]\s*")


def build_command(cmd: str, *args: object) -> str:
    """Format a SCPI command.

    规则：
    - 基础指令会被去除首尾空白并保留原大小写。
    - 附加参数会使用逗号分隔；当参数是 mapping 时，会展开为 ``key=value`` 对。
    - 返回值结尾始终带有换行符，便于串口写入。
    """

    command = cmd.strip()
    if not command:
        raise ValueError("SCPI command must not be empty")

    formatted_args = [fragment for fragment in (_format_arg(arg) for arg in args) if fragment]
    if formatted_args:
        command = f"{command} {','.join(formatted_args)}"
    return f"{command}\n"


def parse_response(raw: str) -> dict[str, Any]:
    """Parse a SCPI response string into a structured dictionary.

    支持以下格式：
    - ``TYPE:key=value,other=1`` → ``{"type": "TYPE", "key": ..., "other": 1}``
    - ``key=value;flag`` → ``{"key": ..., "payload": ["flag"]}``
    - 单个值 → ``{"payload": [value]}``
    数值会尝试转换为 int/float，布尔型（true/false/on/off）统一为 bool。
    """

    text = raw.strip()
    if not text:
        raise ValueError("Empty SCPI response")

    result: dict[str, Any] = {}
    remaining = text

    if ":" in text:
        prefix, candidate = text.split(":", 1)
        if prefix and "=" not in prefix:
            result["type"] = prefix.strip()
            remaining = candidate

    tokens = _tokenize(remaining)
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            result[key.strip()] = _convert_value(value.strip())
        else:
            payload = result.setdefault("payload", [])
            payload.append(_convert_value(token))

    return result


def _tokenize(payload: str) -> Iterable[str]:
    segments: list[str] = []
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        segments.extend(_SEPARATOR_PATTERN.split(line))
    return [segment for segment in segments if segment]


def _format_arg(arg: object) -> str:
    if arg is None:
        return ""
    if isinstance(arg, Mapping):
        parts = [f"{key}={_format_scalar(value)}" for key, value in arg.items() if value is not None]
        return ",".join(parts)
    return _format_scalar(arg)


def _format_scalar(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value)


def _convert_value(token: str) -> Any:
    lowered = token.lower()
    if lowered in {"true", "on", "enable", "enabled"}:
        return True
    if lowered in {"false", "off", "disable", "disabled"}:
        return False
    try:
        if "." in token or "e" in lowered:
            return float(token)
        return int(token)
    except ValueError:
        return token


__all__ = ["build_command", "parse_response"]
