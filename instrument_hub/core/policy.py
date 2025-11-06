from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class DispatchMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    BACKGROUND = "background"


@dataclass(frozen=True, slots=True)
class DispatchPolicy:
    mode: DispatchMode = DispatchMode.SYNC
    priority: int = 0
    name: str | None = None
    run_before: Tuple[str, ...] = ()
    run_after: Tuple[str, ...] = ()
    executor_name: str | None = None
    await_result: bool = True

    @staticmethod
    def default() -> "DispatchPolicy":
        return DispatchPolicy()
