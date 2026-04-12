# aro-plugin-sdk (Python)

Python SDK for building [ARO](https://github.com/arolang/aro) plugins.

## Package layout

```
aro-plugin-sdk-python/
├── pyproject.toml
├── aro_plugin_sdk/
│   ├── __init__.py      # public API
│   ├── decorators.py    # @plugin, @action, @qualifier, @service, @system_object, @on_event
│   ├── input.py         # AROInput — typed JSON accessor
│   ├── output.py        # OutputBuilder, ok()
│   ├── errors.py        # ErrorCode enum, error_response helpers
│   ├── event.py         # EventData class
│   ├── params.py        # Params class
│   ├── runner.py        # run() — persistent JSON-line subprocess loop
│   └── testing.py       # mock_input, mock_http_input
└── tests/
    ├── test_input.py
    └── test_decorators.py
```

## Installation

```bash
pip install aro-plugin-sdk          # from PyPI (once published)
pip install -e .                    # local development
```

## Quick start

```python
from aro_plugin_sdk import plugin, action, qualifier, on_event, run, AROInput

@plugin(name="my-plugin", version="1.0.0", handle="MyPlugin")
class MyPlugin:
    pass

@action(name="greet", verbs=["greet"], role="own", prepositions=["from"],
        description="Greet a person by name")
def handle_greet(input: AROInput):
    name = input.string("name", "World")
    return {"greeting": f"Hello, {name}!"}

@qualifier(name="shout", description="Convert a value to uppercase")
def qualifier_shout(input: AROInput):
    return {"value": input.string("value").upper()}

@on_event("UserCreated")
def on_user_created(input: AROInput):
    user_id = input.string("userId")
    return {"sent_welcome": True, "userId": user_id}

if __name__ == "__main__":
    run()
```

## Key types

### `AROInput`

Typed accessor for the JSON input the ARO runtime sends:

```python
# Direct field lookup (top-level keys win over _with)
input.string("name", "World")      # str
input.int("count", 0)              # int
input.float("price", 0.0)          # float
input.bool("enabled", False)       # bool
input.array("items")               # list
input.dict("meta")                 # dict
input.get("key")                   # Any | None
input.raw()                        # Dict[str, Any]

# With-clause parameters
params = input.with_params()        # Params
params.string("order", "asc")       # str

# Descriptor accessors
input.result_identifier()          # str | None
input.result_qualifier()           # str | None
input.source_identifier()          # str | None
input.preposition()                # str | None
input.context()                    # dict | None
input.context_get("pathParameters")
```

### `OutputBuilder`

Fluent builder for the response dict:

```python
from aro_plugin_sdk import OutputBuilder

response = (
    OutputBuilder()
    .set("result", "hello")
    .set("count", 42)
    .emit("UserCreated", {"id": 1})
    .build()
)
```

### `ErrorCode`

```python
from aro_plugin_sdk import ErrorCode
from aro_plugin_sdk.errors import error_response, missing_error, not_found_error

error_response("Something went wrong", ErrorCode.INTERNAL_ERROR)
missing_error("data")
not_found_error("user/42")
```

## Decorators

| Decorator | Purpose |
|-----------|---------|
| `@plugin(name, version, handle)` | Declare plugin metadata |
| `@action(name, verbs, role, prepositions)` | Register an action handler |
| `@qualifier(name)` | Register a qualifier handler |
| `@service(name)` | Declare a long-running service |
| `@system_object(name)` | Declare a system object |
| `@on_event(event_name)` | Register an event handler |
| `@init` | Plugin initialisation hook |
| `@shutdown` | Plugin shutdown hook |

## JSON-line protocol (`run()`)

The ARO runtime runs Python plugins as a persistent subprocess and communicates
over `stdin` / `stdout` using newline-delimited JSON.

| Request type | Runtime sends | Plugin responds |
|---|---|---|
| `info` | `{"type": "info"}` | Plugin info dict |
| `action` | `{"type": "action", "action": "…", "input": {…}}` | Result dict |
| `qualifier` | `{"type": "qualifier", "qualifier": "…", "input": {…}}` | Result dict |
| `event` | `{"type": "event", "event": "…", "input": {…}}` | `{"results": […]}` |
| `init` | `{"type": "init"}` | `{"ok": true}` |
| `shutdown` | `{"type": "shutdown"}` | `{"ok": true}` (loop exits) |

## Testing

```python
from aro_plugin_sdk.testing import mock_input

def test_greet():
    inp = mock_input({"name": "Alice"})
    result = handle_greet(inp)
    assert result["greeting"] == "Hello, Alice!"
```

Run tests with pytest:

```bash
pip install pytest
pytest
```

## License

MIT
