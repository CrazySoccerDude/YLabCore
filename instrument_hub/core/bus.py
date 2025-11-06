"""Event bus abstractions for the InstruHub platform."""

from __future__ import annotations


class EventBus:  # pragma: no cover - stub
    """Central publish/subscribe bus placeholder."""

    def publish(self, topic: str, payload: object) -> None:
        """Send an event to subscribers (not yet implemented)."""
        raise NotImplementedError

    def subscribe(self, topic: str, callback) -> None:
        """Register a callback for a topic (not yet implemented)."""
        raise NotImplementedError
