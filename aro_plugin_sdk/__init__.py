"""ARO Plugin SDK for Python.

Provides decorators, typed I/O helpers, and a persistent subprocess runner
for building ARO plugins in Python.

Quick start::

    from aro_plugin_sdk import plugin, action, qualifier, on_event, run, ErrorCode
    from aro_plugin_sdk import AROInput

    @plugin(name="my-plugin", version="1.0.0", handle="MyPlugin")
    class MyPlugin:
        pass

    @action(name="greet", verbs=["greet"], role="own", prepositions=["from"])
    def handle_greet(input: AROInput):
        name = input.string("name", "World")
        return {"greeting": f"Hello, {name}!"}

    @qualifier(name="shout")
    def qualifier_shout(input: AROInput):
        return {"value": input.string("value").upper()}

    if __name__ == "__main__":
        run()
"""

from .decorators import (
    action,
    init,
    on_event,
    plugin,
    qualifier,
    service,
    shutdown,
    system_object,
)
from .errors import ErrorCode
from .event import EventData
from .input import AROInput
from .output import OutputBuilder, ok
from .params import Params
from .runner import run

__all__ = [
    # Decorators
    "plugin",
    "action",
    "qualifier",
    "service",
    "system_object",
    "on_event",
    "init",
    "shutdown",
    # Core types
    "AROInput",
    "OutputBuilder",
    "ok",
    "Params",
    "EventData",
    "ErrorCode",
    # Runner
    "run",
]
