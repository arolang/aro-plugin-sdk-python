"""Output helpers for ARO plugin responses.

Every action and qualifier returns a JSON-serialisable dict to the ARO
runtime.  :class:`OutputBuilder` provides a fluent interface for constructing
that dict.

Example::

    from aro_plugin_sdk.output import OutputBuilder

    response = (
        OutputBuilder()
        .set("result", "hello")
        .set("count", 42)
        .emit("DataProcessed", {"count": 42})
        .build()
    )
"""

from typing import Any, Dict, List


class OutputBuilder:
    """Fluent builder for the dict returned by a plugin action or qualifier."""

    def __init__(self) -> None:
        self._fields: Dict[str, Any] = {}
        self._events: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> "OutputBuilder":
        """Set a top-level field in the output dict."""
        self._fields[key] = value
        return self

    def emit(self, event_name: str, payload: Dict[str, Any]) -> "OutputBuilder":
        """Queue an event to be emitted after the action completes.

        The ARO runtime reads the ``_events`` list in the response and
        publishes each entry to the event bus.

        Args:
            event_name: Event name, e.g. ``"UserCreated"``.
            payload: JSON-serialisable payload dict.
        """
        self._events.append({"event": event_name, "payload": payload})
        return self

    def build(self) -> Dict[str, Any]:
        """Return the completed output dict."""
        result: Dict[str, Any] = dict(self._fields)
        if self._events:
            result["_events"] = self._events
        return result


def ok(value: Any = None, **kwargs: Any) -> Dict[str, Any]:
    """Shortcut: return a success dict with a ``"value"`` field.

    Extra keyword arguments are merged in as additional top-level fields::

        ok("hello")                # {"value": "hello"}
        ok(count=42)               # {"count": 42}
        ok("hello", count=42)      # {"value": "hello", "count": 42}
    """
    result: Dict[str, Any] = {}
    if value is not None:
        result["value"] = value
    result.update(kwargs)
    return result
