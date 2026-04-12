"""Error codes and response builders for ARO plugins."""

from enum import IntEnum
from typing import Any, Dict, Optional


class ErrorCode(IntEnum):
    """Numeric error codes understood by the ARO runtime.

    The runtime converts these codes into human-readable diagnostics surfaced
    as "Code is the error message" messages.
    """

    UNKNOWN = 0
    """Generic / unclassified error."""

    MISSING_INPUT = 1
    """A required input field is missing."""

    INVALID_TYPE = 2
    """An input field has an unexpected type."""

    OUT_OF_RANGE = 3
    """A value is outside the permitted range."""

    IO_ERROR = 4
    """An external I/O operation failed."""

    NETWORK_ERROR = 5
    """A network operation failed."""

    SERIALIZATION_ERROR = 6
    """Serialisation or deserialisation failed."""

    NOT_FOUND = 7
    """The requested resource was not found."""

    UNAUTHORIZED = 8
    """The caller is not authorised to perform this operation."""

    TIMEOUT = 9
    """The operation exceeded its time budget."""

    INTERNAL_ERROR = 10
    """An internal plugin error (bug in plugin code)."""


def error_response(
    message: str,
    code: ErrorCode = ErrorCode.UNKNOWN,
) -> Dict[str, Any]:
    """Build a JSON-serialisable error response dict.

    Args:
        message: Human-readable description of the error.
        code: Machine-readable :class:`ErrorCode`.

    Returns:
        A dict with ``"error"`` and ``"code"`` keys understood by the runtime.
    """
    return {"error": message, "code": int(code)}


def missing_error(field: str) -> Dict[str, Any]:
    """Shortcut for :data:`ErrorCode.MISSING_INPUT`."""
    return error_response(f"Missing required field: {field}", ErrorCode.MISSING_INPUT)


def invalid_type_error(field: str, expected: str) -> Dict[str, Any]:
    """Shortcut for :data:`ErrorCode.INVALID_TYPE`."""
    return error_response(
        f"Field '{field}' must be {expected}", ErrorCode.INVALID_TYPE
    )


def not_found_error(resource: str) -> Dict[str, Any]:
    """Shortcut for :data:`ErrorCode.NOT_FOUND`."""
    return error_response(f"Not found: {resource}", ErrorCode.NOT_FOUND)


def internal_error(message: str) -> Dict[str, Any]:
    """Shortcut for :data:`ErrorCode.INTERNAL_ERROR`."""
    return error_response(message, ErrorCode.INTERNAL_ERROR)
