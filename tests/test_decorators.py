"""Tests for aro_plugin_sdk decorators and the runner protocol."""

import io
import json

import pytest

import aro_plugin_sdk.decorators as _dec
from aro_plugin_sdk import AROInput, ErrorCode, action, on_event, plugin, qualifier, run
from aro_plugin_sdk.decorators import get_plugin_info
from aro_plugin_sdk.testing import mock_input


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset the decorator registry before each test."""
    _dec._reset_registry()
    yield
    _dec._reset_registry()


# ---------------------------------------------------------------------------
# @plugin
# ---------------------------------------------------------------------------

class TestPluginDecorator:
    def test_sets_plugin_meta(self):
        @plugin(name="test-plugin", version="2.0.0", handle="TestPlugin")
        class TestPlugin:
            pass

        info = get_plugin_info()
        assert info["name"] == "test-plugin"
        assert info["version"] == "2.0.0"
        assert info["handle"] == "TestPlugin"

    def test_handle_defaults_to_name(self):
        @plugin(name="my-plugin")
        class P:
            pass

        info = get_plugin_info()
        assert info["handle"] == "my-plugin"


# ---------------------------------------------------------------------------
# @action
# ---------------------------------------------------------------------------

class TestActionDecorator:
    def test_registers_action(self):
        @action(name="greet", verbs=["greet"], role="own", prepositions=["from"])
        def handle_greet(inp: AROInput):
            return {"greeting": f"Hello, {inp.string('name')}!"}

        info = get_plugin_info()
        assert len(info["actions"]) == 1
        assert info["actions"][0]["name"] == "greet"

    def test_action_callable(self):
        @action(name="greet", verbs=["greet"])
        def handle_greet(inp: AROInput):
            return {"greeting": f"Hello, {inp.string('name', 'World')}!"}

        fn = _dec.get_action("greet")
        assert fn is not None
        result = fn(mock_input({"name": "Alice"}))
        assert result["greeting"] == "Hello, Alice!"

    def test_action_callable_by_verb(self):
        @action(name="my-action", verbs=["doThing"])
        def handle(inp):
            return {"ok": True}

        assert _dec.get_action("doThing") is not None
        assert _dec.get_action("my-action") is not None

    def test_unknown_action_returns_none(self):
        assert _dec.get_action("nonexistent") is None

    def test_internal_fn_not_in_info(self):
        @action(name="x")
        def x(inp):
            return {}

        info = get_plugin_info()
        for a in info["actions"]:
            assert "_fn" not in a


# ---------------------------------------------------------------------------
# @qualifier
# ---------------------------------------------------------------------------

class TestQualifierDecorator:
    def test_registers_qualifier(self):
        @qualifier(name="shout")
        def q_shout(inp):
            return {"value": inp.string("value").upper()}

        info = get_plugin_info()
        assert len(info["qualifiers"]) == 1
        assert info["qualifiers"][0]["name"] == "shout"

    def test_qualifier_callable(self):
        @qualifier(name="shout")
        def q_shout(inp):
            return {"value": inp.string("value").upper()}

        fn = _dec.get_qualifier("shout")
        assert fn is not None
        result = fn(mock_input({"value": "hello"}))
        assert result["value"] == "HELLO"


# ---------------------------------------------------------------------------
# @on_event
# ---------------------------------------------------------------------------

class TestOnEventDecorator:
    def test_registers_event_handler(self):
        @on_event("UserCreated")
        def handle_user(inp):
            return {"handled": True}

        handlers = _dec.get_event_handlers("UserCreated")
        assert len(handlers) == 1

    def test_multiple_handlers_for_same_event(self):
        @on_event("Tick")
        def h1(inp):
            return {"h": 1}

        @on_event("Tick")
        def h2(inp):
            return {"h": 2}

        handlers = _dec.get_event_handlers("Tick")
        assert len(handlers) == 2

    def test_no_handlers_returns_empty(self):
        assert _dec.get_event_handlers("Unknown") == []


# ---------------------------------------------------------------------------
# run() — JSON-line protocol
# ---------------------------------------------------------------------------

def _run_messages(*messages) -> list:
    """Feed messages to run() and collect responses."""
    stdin = io.StringIO("\n".join(json.dumps(m) for m in messages) + "\n")
    stdout = io.StringIO()
    run(stdin=stdin, stdout=stdout)
    lines = [l for l in stdout.getvalue().splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


class TestRunner:
    def test_info_message(self):
        @plugin(name="runner-test", version="1.0.0", handle="RT")
        class P:
            pass

        responses = _run_messages({"type": "info"})
        assert responses[0]["name"] == "runner-test"

    def test_action_dispatch(self):
        @action(name="add", verbs=["add"])
        def handle_add(inp: AROInput):
            a = inp.int("a")
            b = inp.int("b")
            return {"sum": a + b}

        responses = _run_messages(
            {"type": "action", "action": "add", "input": {"a": 3, "b": 4}}
        )
        assert responses[0]["sum"] == 7

    def test_unknown_action_returns_error(self):
        responses = _run_messages(
            {"type": "action", "action": "nonexistent", "input": {}}
        )
        assert "error" in responses[0]
        assert responses[0]["code"] == int(ErrorCode.NOT_FOUND)

    def test_qualifier_dispatch(self):
        @qualifier(name="upper")
        def q_upper(inp: AROInput):
            return {"value": inp.string("value").upper()}

        responses = _run_messages(
            {"type": "qualifier", "qualifier": "upper", "input": {"value": "hello"}}
        )
        assert responses[0]["value"] == "HELLO"

    def test_event_dispatch(self):
        @on_event("Ping")
        def handle_ping(inp):
            return {"pong": True}

        responses = _run_messages(
            {"type": "event", "event": "Ping", "input": {}}
        )
        assert responses[0]["results"][0]["pong"] is True

    def test_shutdown_stops_loop(self):
        # Shutdown message should stop reading further messages
        responses = _run_messages(
            {"type": "shutdown"},
            {"type": "info"},   # should not be processed
        )
        assert len(responses) == 1
        assert responses[0].get("ok") is True

    def test_invalid_json_returns_error(self):
        stdin = io.StringIO("not-json\n")
        stdout = io.StringIO()
        run(stdin=stdin, stdout=stdout)
        lines = [l for l in stdout.getvalue().splitlines() if l.strip()]
        assert len(lines) == 1
        resp = json.loads(lines[0])
        assert "error" in resp

    def test_init_message(self):
        called = []

        from aro_plugin_sdk import init as aro_init

        @aro_init
        def my_init():
            called.append(True)

        responses = _run_messages({"type": "init"})
        assert responses[0].get("ok") is True
        assert called == [True]
