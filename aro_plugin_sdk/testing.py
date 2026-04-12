"""Test helpers for ARO plugin unit tests."""

from typing import Any, Dict, Optional

from .input import AROInput


def mock_input(data: Dict[str, Any]) -> AROInput:
    """Build an :class:`~aro_plugin_sdk.AROInput` from a plain dict.

    This is the primary test helper.  Pass a dict for the full input payload
    (top-level fields plus optional ``_with``).

    Example::

        from aro_plugin_sdk.testing import mock_input

        def test_greet():
            inp = mock_input({"name": "Alice", "_with": {"loud": True}})
            assert inp.string("name") == "Alice"
            assert inp.with_params().bool("loud") is True
    """
    return AROInput(data)


def mock_http_input(
    path_params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> AROInput:
    """Build an :class:`~aro_plugin_sdk.AROInput` that simulates an HTTP request.

    Args:
        path_params: Values injected into ``context.pathParameters``.
        body: Request body placed in ``context.body``.
        extra: Additional top-level fields merged into the input.

    Example::

        inp = mock_http_input(
            path_params={"id": "42"},
            body={"name": "Alice"},
        )
        assert inp.context_get("pathParameters") == {"id": "42"}
    """
    data: Dict[str, Any] = dict(extra or {})
    data["context"] = {
        "pathParameters": path_params or {},
        "body": body or {},
    }
    return AROInput(data)
