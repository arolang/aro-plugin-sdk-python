"""Event data passed to ``@on_event`` handlers."""

from typing import Any, Dict, List, Optional


class EventData:
    """Payload delivered to an event handler registered with :func:`on_event`.

    The ARO runtime serialises the event as a JSON envelope::

        { "event": "UserCreated", "payload": { ... } }

    :class:`EventData` gives typed access to the common envelope fields and
    the payload contents.
    """

    def __init__(self, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._name = name
        self._payload: Dict[str, Any] = payload or {}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EventData":
        """Construct from the JSON envelope dict the runtime sends."""
        name = d.get("event", "")
        payload = d.get("payload") or {}
        return cls(name=name, payload=payload)

    @property
    def name(self) -> str:
        """The event name, e.g. ``"UserCreated"``."""
        return self._name

    @property
    def payload(self) -> Dict[str, Any]:
        """The raw payload dict."""
        return self._payload

    def get(self, key: str, default: Any = None) -> Any:
        """Return a field from the payload."""
        return self._payload.get(key, default)

    def string(self, key: str, default: str = "") -> str:
        """Return a string field, coercing if necessary."""
        v = self._payload.get(key)
        if v is None:
            return default
        return str(v)

    def int(self, key: str, default: int = 0) -> int:
        """Return an integer field."""
        v = self._payload.get(key)
        if v is None:
            return default
        return int(v)

    def bool(self, key: str, default: bool = False) -> bool:
        """Return a boolean field."""
        v = self._payload.get(key)
        if v is None:
            return default
        return bool(v)

    def list(self, key: str) -> List[Any]:
        """Return a list field."""
        v = self._payload.get(key)
        if isinstance(v, list):
            return v
        return []

    def __repr__(self) -> str:
        return f"EventData(name={self._name!r}, payload={self._payload!r})"
