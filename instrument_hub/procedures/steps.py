"""Definitions for individual procedure steps."""

from __future__ import annotations


class ProcedureStep:  # pragma: no cover - stub
    """Base class for all procedure steps."""

    def run(self) -> None:
        """Execute the step logic."""
        raise NotImplementedError
