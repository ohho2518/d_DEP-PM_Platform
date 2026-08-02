"""In-process Message Bus (ADR-03)."""
from app.bus.dispatcher import clear_subscribers, publish, subscribe

__all__ = ["publish", "subscribe", "clear_subscribers"]
