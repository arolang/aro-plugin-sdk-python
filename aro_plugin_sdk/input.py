"""Typed wrapper around the JSON payload the ARO runtime sends to a plugin."""

from typing import Any, Dict, List, Optional

from .params import Params


class AROInput:
    """Typed accessor for the JSON input passed to an ARO plugin action or qualifier.

    The runtime serialises the execution context as a JSON object with these
    top-level keys:

    +-------------------+----------------------------------------------+
    | Key               | Description                                  |
    +===================+==============================================+
    | ``result``        | Result descriptor (identifier, qualifier)    |
    +-------------------+----------------------------------------------+
    | ``object``        | Object/source descriptor                     |
    +-------------------+----------------------------------------------+
    | ``preposition``   | Preposition keyword (``"from"``, ``"with"``) |
    +-------------------+----------------------------------------------+
    | ``context``       | Ambient runtime context values               |
    +-------------------+----------------------------------------------+
    | ``_with``         | Values from the ``with``-clause              |
    +-------------------+----------------------------------------------+
    | *everything else* | Direct binding values                        |
    +-------------------+----------------------------------------------+

    Example::

        input = AROInput({"data": "hello", "count": 3, "_with": {"flag": True}})
        input.string("data")       # "hello"
        input.int("count")         # 3
        input.with_params().bool("flag")  # True
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def from_json(cls, json_str: str) -> "AROInput":
        """Parse from a JSON string."""
        import json
        return cls(json.loads(json_str))

    # ------------------------------------------------------------------
    # Field lookup (top-level wins over _with)
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the raw value for *key*, checking top-level then ``_with``."""
        if key in self._data:
            return self._data[key]
        with_obj = self._data.get("_with")
        if isinstance(with_obj, dict) and key in with_obj:
            return with_obj[key]
        return default

    def string(self, key: str, default: str = "") -> str:
        """Return a string value for *key*."""
        v = self.get(key)
        if v is None:
            return default
        return str(v)

    def int(self, key: str, default: int = 0) -> int:
        """Return an integer value for *key*."""
        v = self.get(key)
        if v is None:
            return default
        return int(v)

    def float(self, key: str, default: float = 0.0) -> float:
        """Return a float value for *key*."""
        v = self.get(key)
        if v is None:
            return default
        return float(v)

    def bool(self, key: str, default: bool = False) -> bool:
        """Return a boolean value for *key*."""
        v = self.get(key)
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes")
        return bool(v)

    def array(self, key: str) -> List[Any]:
        """Return a list value for *key*, or an empty list if absent."""
        v = self.get(key)
        if isinstance(v, list):
            return v
        return []

    def dict(self, key: str) -> Dict[str, Any]:
        """Return a dict value for *key*, or an empty dict if absent."""
        v = self.get(key)
        if isinstance(v, dict):
            return v
        return {}

    def raw(self) -> Dict[str, Any]:
        """Return the entire raw input dict."""
        return self._data

    # ------------------------------------------------------------------
    # With-clause
    # ------------------------------------------------------------------

    def with_params(self) -> Params:
        """Return the ``_with`` object as a :class:`~aro_plugin_sdk.Params`."""
        with_obj = self._data.get("_with")
        if isinstance(with_obj, dict):
            return Params.from_dict(with_obj)
        return Params.empty()

    # ------------------------------------------------------------------
    # Descriptor accessors
    # ------------------------------------------------------------------

    def result_descriptor(self) -> Optional[Dict[str, Any]]:
        """Return the result descriptor dict, if present."""
        v = self._data.get("result")
        return v if isinstance(v, dict) else None

    def result_identifier(self) -> Optional[str]:
        """Return the identifier the runtime will bind the result to."""
        d = self.result_descriptor()
        return d.get("identifier") if d else None

    def result_qualifier(self) -> Optional[str]:
        """Return the result qualifier, if any."""
        d = self.result_descriptor()
        return d.get("qualifier") if d else None

    def source_descriptor(self) -> Optional[Dict[str, Any]]:
        """Return the object/source descriptor dict, if present."""
        v = self._data.get("object")
        return v if isinstance(v, dict) else None

    def source_identifier(self) -> Optional[str]:
        """Return the source identifier."""
        d = self.source_descriptor()
        return d.get("identifier") if d else None

    def source_qualifier(self) -> Optional[str]:
        """Return the source qualifier, if any."""
        d = self.source_descriptor()
        return d.get("qualifier") if d else None

    def preposition(self) -> Optional[str]:
        """Return the preposition keyword, e.g. ``"from"`` or ``"with"``."""
        return self._data.get("preposition")

    def context(self) -> Optional[Dict[str, Any]]:
        """Return the ambient execution context dict."""
        v = self._data.get("context")
        return v if isinstance(v, dict) else None

    def context_get(self, key: str, default: Any = None) -> Any:
        """Return a field from inside the context object."""
        ctx = self.context()
        if ctx is None:
            return default
        return ctx.get(key, default)

    def __repr__(self) -> str:
        return f"AROInput({self._data!r})"
