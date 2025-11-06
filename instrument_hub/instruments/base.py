"""Base classes and interfaces for instruments."""

from __future__ import annotations


class Instrument:  # pragma: no cover - stub
    """Minimal instrument interface placeholder."""

    def execute(self, command: str) -> None:
        """Execute a command on the instrument."""
        raise NotImplementedError

    def on_bytes(self, payload: bytes) -> None:
        """Handle inbound bytes from the transport."""
        raise NotImplementedError
