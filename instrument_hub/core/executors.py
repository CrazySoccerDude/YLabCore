from __future__ import annotations

from concurrent.futures import Executor, ThreadPoolExecutor
from threading import RLock
from typing import Dict


class ExecutorRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._default: Executor | None = None
        self._executors: Dict[str, Executor] = {}

    def get(self, name: str | None = None) -> Executor:
        with self._lock:
            if name is None:
                if self._default is None:
                    self._default = ThreadPoolExecutor()
                return self._default
            try:
                return self._executors[name]
            except KeyError as exc:
                raise KeyError(f"Unknown executor '{name}'") from exc

    def register(self, name: str, executor: Executor, *, replace: bool = False) -> None:
        with self._lock:
            if not replace and name in self._executors:
                raise ValueError(f"Executor '{name}' already registered")
            self._executors[name] = executor

    def unregister(self, name: str) -> Executor | None:
        with self._lock:
            return self._executors.pop(name, None)

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            executors = list(self._executors.values())
            default = self._default
            self._executors.clear()
            self._default = None
        for executor in executors:
            if hasattr(executor, "shutdown"):
                executor.shutdown(wait=wait)
        if default is not None and hasattr(default, "shutdown"):
            default.shutdown(wait=wait)
