"""Persistent subprocess runner for ARO Python plugins.

The ARO runtime runs Python plugins as a long-lived subprocess and
communicates over ``stdin`` / ``stdout`` using a newline-delimited JSON
(JSON-line) protocol.

Protocol
--------
Every message is a single JSON object followed by ``\\n``.

Request format (runtime -> plugin)::

    { "type": "info" }
    { "type": "action",    "action": "my-action", "input": { ... } }
    { "type": "qualifier", "qualifier": "shout",   "input": { ... } }
    { "type": "event",     "event":  "UserCreated","input": { ... } }
    { "type": "init" }
    { "type": "shutdown" }

Response format (plugin -> runtime)::

    { "result": { ... } }      # success
    { "error": "…", "code": 0 } # failure

Usage
-----
Call :func:`run` at the end of your plugin module::

    if __name__ == "__main__":
        from aro_plugin_sdk import run
        run()
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, TextIO

from .decorators import (
    get_action,
    get_event_handlers,
    get_plugin_info,
    get_qualifier,
    _init_fn,
    _shutdown_fn,
)
from .errors import ErrorCode, error_response
from .input import AROInput


def _handle_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a single protocol message and return the response dict."""
    msg_type = message.get("type", "")

    if msg_type == "info":
        return get_plugin_info()

    if msg_type == "init":
        from . import decorators as _dec
        if _dec._init_fn is not None:
            try:
                _dec._init_fn()
            except Exception as exc:
                return error_response(str(exc), ErrorCode.INTERNAL_ERROR)
        return {"ok": True}

    if msg_type == "shutdown":
        from . import decorators as _dec
        if _dec._shutdown_fn is not None:
            try:
                _dec._shutdown_fn()
            except Exception as exc:
                return error_response(str(exc), ErrorCode.INTERNAL_ERROR)
        return {"ok": True}

    if msg_type == "action":
        action_name = message.get("action", "")
        fn = get_action(action_name)
        if fn is None:
            return error_response(
                f"Unknown action: {action_name}", ErrorCode.NOT_FOUND
            )
        input_data = message.get("input", {})
        aro_input = AROInput(input_data)
        try:
            result = fn(aro_input)
            if isinstance(result, dict):
                return result
            return {"value": result}
        except Exception as exc:
            return error_response(str(exc), ErrorCode.INTERNAL_ERROR)

    if msg_type == "qualifier":
        qualifier_name = message.get("qualifier", "")
        fn = get_qualifier(qualifier_name)
        if fn is None:
            return error_response(
                f"Unknown qualifier: {qualifier_name}", ErrorCode.NOT_FOUND
            )
        input_data = message.get("input", {})
        aro_input = AROInput(input_data)
        try:
            result = fn(aro_input)
            if isinstance(result, dict):
                return result
            return {"value": result}
        except Exception as exc:
            return error_response(str(exc), ErrorCode.INTERNAL_ERROR)

    if msg_type == "event":
        event_name = message.get("event", "")
        handlers = get_event_handlers(event_name)
        if not handlers:
            # Events with no handler are silently ignored
            return {"ok": True}
        input_data = message.get("input", {})
        aro_input = AROInput(input_data)
        results = []
        for fn in handlers:
            try:
                result = fn(aro_input)
                results.append(result if isinstance(result, dict) else {"value": result})
            except Exception as exc:
                results.append(error_response(str(exc), ErrorCode.INTERNAL_ERROR))
        return {"results": results}

    return error_response(f"Unknown message type: {msg_type!r}", ErrorCode.UNKNOWN)


def run(
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> None:
    """Enter the persistent JSON-line read-eval loop.

    Reads one JSON object per line from *stdin*, dispatches it, and writes the
    response as a single JSON line to *stdout*.

    This function blocks until *stdin* is closed (EOF) or a ``shutdown``
    message is received.

    Args:
        stdin: Input stream (default ``sys.stdin``).
        stdout: Output stream (default ``sys.stdout``).
    """
    for line in stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response = error_response(
                f"Invalid JSON: {exc}", ErrorCode.SERIALIZATION_ERROR
            )
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
            continue

        response = _handle_message(message)
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()

        # Honour explicit shutdown request
        if message.get("type") == "shutdown":
            break
