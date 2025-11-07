"""占位：通用重试/退避策略。"""

from __future__ import annotations


def exponential_backoff(attempt: int, base: float = 0.5, factor: float = 2.0) -> float:
    """占位公式：后续根据业务调整。"""
    return base * (factor ** max(0, attempt - 1))
