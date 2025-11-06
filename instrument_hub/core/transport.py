"""Transport layer abstractions for device I/O."""

from __future__ import annotations

from typing import Protocol


class Transport(Protocol):
    """Protocol describing the minimal transport interface."""

    def open(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError

    def write(self, data: bytes) -> None:  # pragma: no cover - stub
        raise NotImplementedError
