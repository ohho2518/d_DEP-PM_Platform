"""In-process Message Bus (ADR-03)."""
from app.bus.dispatcher import publish, subscribe, clear_subscribers

__all__ = ["publish", "subscribe", "clear_subscribers"]
