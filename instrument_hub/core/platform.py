"""Platform loader and lifecycle management stubs."""

from __future__ import annotations


class Platform:  # pragma: no cover - stub
    """Placeholder class responsible for coordinating transports and instruments."""

    def load_from_config(self, config_path: str) -> None:
        """Load platform configuration from a YAML file."""
        raise NotImplementedError

    def start(self) -> None:
        """Start platform services."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop platform services."""
        raise NotImplementedError
