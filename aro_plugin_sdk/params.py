"""With-clause and qualifier parameter types."""

from typing import Any, Dict, List, Optional


class Params:
    """Key-value parameters supplied via the ARO ``with``-clause.

    In ARO source code::

        Compute the <sorted: Stats.sort with <order: "desc">> from the <numbers>.

    The ``Params`` object gives typed access to those ``with``-clause values.
    It is also used to pass per-invocation parameters to qualifier handlers.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        self._data: Dict[str, Any] = data or {}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Params":
        """Construct from an arbitrary dict."""
        return cls(data=d)

    @classmethod
    def empty(cls) -> "Params":
        """Return an empty :class:`Params`."""
        return cls()

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the raw value for *key*."""
        return self._data.get(key, default)

    def string(self, key: str, default: str = "") -> str:
        """Return a string parameter."""
        v = self._data.get(key)
        if v is None:
            return default
        return str(v)

    def int(self, key: str, default: int = 0) -> int:
        """Return an integer parameter."""
        v = self._data.get(key)
        if v is None:
            return default
        return int(v)

    def float(self, key: str, default: float = 0.0) -> float:
        """Return a float parameter."""
        v = self._data.get(key)
        if v is None:
            return default
        return float(v)

    def bool(self, key: str, default: bool = False) -> bool:
        """Return a boolean parameter."""
        v = self._data.get(key)
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes")
        return bool(v)

    def list(self, key: str) -> List[Any]:
        """Return a list parameter."""
        v = self._data.get(key)
        if isinstance(v, list):
            return v
        return []

    def contains(self, key: str) -> bool:
        """Return ``True`` if *key* is present in the params."""
        return key in self._data

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Params({self._data!r})"
