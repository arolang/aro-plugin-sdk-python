# ARO Plugin SDK for Python

Build ARO plugins in Python with decorators. No C code, no FFI — just decorate your functions and the SDK handles communication with the ARO runtime automatically.

## Installation

```bash
pip install aro-plugin-sdk                                          # from PyPI
pip install git+https://github.com/arolang/aro-plugin-sdk-python    # from GitHub
```

Or add to your plugin's `requirements.txt`:

```
aro-plugin-sdk @ git+https://github.com/arolang/aro-plugin-sdk-python.git@main
```

## Quick Start

```python
from aro_plugin_sdk import plugin, action, export_abi, run, AROInput

@plugin(name="my-plugin", version="1.0.0", handle="Greeting")
class MyPlugin:
    pass

@action(name="greet", verbs=["greet"], role="own", prepositions=["with"],
        description="Greet someone by name")
def handle_greet(input: AROInput):
    name = input.string("name", "World")
    return {"greeting": f"Hello, {name}!"}

export_abi(globals())

if __name__ == "__main__":
    run()
```

**Important**: `export_abi(globals())` must be called at module level after all handlers are defined. It generates the C ABI bridge functions the ARO runtime expects.

## Actions

Actions handle verbs in ARO statements. Decorate functions with `@action`:

```python
@action(name="parse-csv", verbs=["parsecsv", "readcsv"], role="own",
        prepositions=["from", "with"],
        description="Parse CSV data into rows")
def handle_parse_csv(input: AROInput):
    data = input.string("data")
    has_headers = input.bool("headers", True)

    rows = parse(data, headers=has_headers)
    return {"rows": rows, "count": len(rows)}
```

Handler naming convention: `handle_<action_name>` (dashes become underscores).

**Roles**: `"request"`, `"own"`, `"response"`, `"export"`

## Qualifiers

Qualifiers transform values using `<value: Handle.qualifier>` syntax in ARO:

```python
@qualifier(name="sort", description="Sort a list in ascending order")
def qualifier_sort(input: AROInput):
    value = input.get("value")
    if not isinstance(value, list):
        return {"error": "sort requires a list"}
    return {"result": sorted(value)}

@qualifier(name="unique", description="Remove duplicate elements")
def qualifier_unique(input: AROInput):
    value = input.get("value")
    if not isinstance(value, list):
        return {"error": "unique requires a list"}
    seen = set()
    unique = [x for x in value if not (x in seen or seen.add(x))]
    return {"result": unique}
```

Qualifier naming convention: `qualifier_<name>`.

Return `{"result": value}` for success or `{"error": "message"}` for failure.

## Services

Services expose methods callable via `Call the <result> from the <service: method>.`

```python
@service(name="cache", description="In-memory key-value cache")
class CacheService:
    pass

@action(name="cache-set", verbs=["cacheset"], role="own", prepositions=["with"])
def handle_cache_set(input: AROInput):
    key = input.with_params().string("key")
    value = input.with_params().get("value")
    cache[key] = value
    return {"stored": True}
```

## Event Handlers

React to events emitted by other plugins or ARO feature sets:

```python
@on_event("UserCreated")
def on_user_created(input: AROInput):
    user_id = input.string("userId")
    send_welcome_email(user_id)
    return {"sent_welcome": True}
```

## Lifecycle Hooks

```python
from aro_plugin_sdk import init, shutdown

@init
def on_init():
    """Called once when the plugin is loaded."""
    connect_to_database()

@shutdown
def on_shutdown():
    """Called when the plugin is unloaded."""
    close_database()
```

## Input API

`AROInput` provides type-safe access to the JSON envelope:

```python
# Primary data (top-level keys take precedence over _with)
input.string("name", "default")    # str
input.int("count", 0)              # int
input.float("price", 0.0)          # float
input.bool("enabled", False)       # bool
input.array("items")               # list
input.dict("metadata")             # dict
input.get("key")                   # Any | None
input.raw()                        # Dict[str, Any]

# With-clause parameters: with { format: "json", limit: 10 }
params = input.with_params()        # Params
params.string("format", "text")     # str
params.int("limit", 10)             # int
params.bool("verbose", False)       # bool
params.contains("key")              # bool

# ARO statement descriptors
input.result_identifier()          # str | None — e.g. "greeting"
input.result_qualifier()           # str | None — e.g. "formal"
input.source_identifier()          # str | None — e.g. "user-data"
input.preposition()                # str | None — e.g. "with"

# Execution context
input.context()                    # dict | None
input.context_get("requestId")     # Any | None
input.context_get("featureSet")    # Any | None
```

## Output

Return a plain dictionary from handlers. Use `OutputBuilder` for complex responses:

```python
# Simple return (most common)
return {"greeting": f"Hello, {name}!"}

# With event emission
from aro_plugin_sdk import OutputBuilder

return (
    OutputBuilder()
    .set("user", user)
    .emit("UserCreated", {"userId": user["id"]})
    .build()
)

# Shortcut
from aro_plugin_sdk import ok
return ok(greeting=f"Hello, {name}!")
```

## Error Handling

```python
from aro_plugin_sdk import ErrorCode
from aro_plugin_sdk.errors import error_response, missing_error, not_found_error

# Return errors from handlers
return missing_error("data")                                    # code 1
return not_found_error("user/42")                              # code 7
return error_response("Something broke", ErrorCode.INTERNAL_ERROR)  # code 10
```

| Code | Name | Description |
|------|------|-------------|
| 0 | `UNKNOWN` | Generic error |
| 1 | `MISSING_INPUT` | Required field missing |
| 2 | `INVALID_TYPE` | Type mismatch |
| 3 | `OUT_OF_RANGE` | Value out of range |
| 4 | `IO_ERROR` | I/O operation failed |
| 5 | `NETWORK_ERROR` | Network/connection error |
| 6 | `SERIALIZATION_ERROR` | JSON encoding error |
| 7 | `NOT_FOUND` | Resource not found |
| 8 | `UNAUTHORIZED` | Access denied |
| 9 | `TIMEOUT` | Operation timed out |
| 10 | `INTERNAL_ERROR` | Plugin bug |

## Testing

```python
from aro_plugin_sdk.testing import mock_input

def test_greet():
    inp = mock_input({"name": "Alice"})
    result = handle_greet(inp)
    assert result["greeting"] == "Hello, Alice!"

def test_with_params():
    inp = mock_input({"data": "hello", "_with": {"format": "json"}})
    params = inp.with_params()
    assert params.string("format") == "json"
```

Run with pytest:
```bash
pip install pytest
pytest
```

## How It Works

The ARO runtime launches Python plugins as persistent subprocesses and communicates via stdin/stdout using newline-delimited JSON:

| Request | Runtime sends | Plugin responds |
|---------|--------------|-----------------|
| `info` | `{"type": "info"}` | Plugin metadata |
| `action` | `{"type": "action", "action": "greet", "input": {...}}` | Result dict |
| `qualifier` | `{"type": "qualifier", "qualifier": "sort", "input": {...}}` | `{"result": [...]}` |
| `event` | `{"type": "event", "event": "UserCreated", "input": {...}}` | Result dict |
| `init` | `{"type": "init"}` | `{"ok": true}` |
| `shutdown` | `{"type": "shutdown"}` | `{"ok": true}` |

`export_abi(globals())` generates module-level functions that the runner dispatches to your decorated handlers. `run()` starts the JSON-line loop.

## Complete Example

```python
from typing import Any, Dict, List
from aro_plugin_sdk import (
    AROInput, OutputBuilder, plugin, action, qualifier,
    init, shutdown, export_abi, run,
)

@plugin(name="plugin-python-stats", version="1.0.0", handle="Stats")
class StatsPlugin:
    pass

_data_store: List[float] = []

@init
def on_init():
    _data_store.clear()

@action(name="add-values", verbs=["addvalues"], role="own",
        prepositions=["from", "with"],
        description="Add values to the data store")
def handle_add_values(input: AROInput):
    values = input.array("data") or input.array("values") or []
    _data_store.extend(float(v) for v in values)
    return {"count": len(_data_store)}

@qualifier(name="avg", description="Compute average of a numeric list")
def qualifier_avg(input: AROInput):
    value = input.get("value")
    if not isinstance(value, list) or not value:
        return {"error": "avg requires a non-empty numeric list"}
    return {"result": sum(float(v) for v in value) / len(value)}

@qualifier(name="sum", description="Compute sum of a numeric list")
def qualifier_sum(input: AROInput):
    value = input.get("value")
    if not isinstance(value, list):
        return {"error": "sum requires a list"}
    return {"result": sum(float(v) for v in value)}

@shutdown
def on_shutdown():
    _data_store.clear()

export_abi(globals())

if __name__ == "__main__":
    run()
```

## License

MIT
