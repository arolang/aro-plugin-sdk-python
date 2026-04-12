"""Decorators for declaring ARO plugin components.

Decorators do two things:
1. They attach metadata to the decorated function or class so that the SDK
   registry can collect it.
2. They are harvested by :func:`~aro_plugin_sdk.run` to build the
   ``aro_plugin_info()`` response automatically.

Usage example::

    from aro_plugin_sdk import plugin, action, qualifier, on_event, run

    @plugin(name="my-plugin", version="1.0.0", handle="MyPlugin")
    class MyPlugin:
        pass

    @action(name="greet", verbs=["greet"], role="own", prepositions=["from"])
    def handle_greet(input):
        name = input.string("name", "World")
        return {"greeting": f"Hello, {name}!"}

    @qualifier(name="shout")
    def qualifier_shout(input):
        return {"value": input.string("value").upper()}

    if __name__ == "__main__":
        run()
"""

from typing import Any, Callable, Dict, List, Optional, Type

# ---------------------------------------------------------------------------
# Internal registry — populated at import time by decorators.
# ---------------------------------------------------------------------------

_plugin_meta: Optional[Dict[str, Any]] = None
_actions: List[Dict[str, Any]] = []
_qualifiers: List[Dict[str, Any]] = []
_services: List[Dict[str, Any]] = []
_system_objects: List[Dict[str, Any]] = []
_event_handlers: List[Dict[str, Any]] = []
_init_fn: Optional[Callable] = None
_shutdown_fn: Optional[Callable] = None

# action/qualifier name -> callable
_action_registry: Dict[str, Callable] = {}
_qualifier_registry: Dict[str, Callable] = {}
_event_registry: Dict[str, List[Callable]] = {}


def _reset_registry() -> None:
    """Clear all registered components (for testing)."""
    global _plugin_meta, _actions, _qualifiers, _services
    global _system_objects, _event_handlers, _init_fn, _shutdown_fn
    global _action_registry, _qualifier_registry, _event_registry

    _plugin_meta = None
    _actions = []
    _qualifiers = []
    _services = []
    _system_objects = []
    _event_handlers = []
    _init_fn = None
    _shutdown_fn = None
    _action_registry = {}
    _qualifier_registry = {}
    _event_registry = {}


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def plugin(
    name: str,
    version: str = "1.0.0",
    handle: str = "",
    description: str = "",
) -> Callable:
    """Declare plugin-level metadata.

    Apply this decorator to a class or module-level dummy class that acts as
    the plugin's namespace.

    Args:
        name: Plugin name, e.g. ``"my-plugin"``.
        version: Semantic version string.
        handle: Namespace handle used in ARO source, e.g. ``"MyPlugin"``.
        description: Human-readable description.
    """

    def decorator(cls: type) -> type:
        global _plugin_meta
        _plugin_meta = {
            "name": name,
            "version": version,
            "handle": handle or name,
            "description": description,
        }
        cls.__aro_plugin_meta__ = _plugin_meta
        return cls

    return decorator


def action(
    name: str,
    verbs: Optional[List[str]] = None,
    role: str = "own",
    prepositions: Optional[List[str]] = None,
    description: str = "",
) -> Callable:
    """Register a function as an ARO action handler.

    Args:
        name: Action name, e.g. ``"my-action"``.
        verbs: List of verb strings the runtime uses to dispatch.
        role: Action role: ``"own"``, ``"request"``, ``"response"``,
              or ``"export"``.
        prepositions: Accepted prepositions, e.g. ``["from", "with"]``.
        description: Human-readable description.
    """

    def decorator(fn: Callable) -> Callable:
        meta = {
            "name": name,
            "verbs": verbs or [name.replace("-", "").lower()],
            "role": role,
            "prepositions": prepositions or ["from"],
            "description": description,
            "_fn": fn,
        }
        _actions.append(meta)
        # Register all verb forms
        for verb in meta["verbs"]:
            _action_registry[verb] = fn
        # Also register by canonical name
        _action_registry[name] = fn
        fn.__aro_action__ = meta
        return fn

    return decorator


def qualifier(
    name: str,
    description: str = "",
) -> Callable:
    """Register a function as an ARO qualifier handler.

    Qualifiers transform a single value and are invoked via the
    ``<value: Handle.qualifier>`` syntax.

    Args:
        name: Qualifier name, e.g. ``"reverse"``.
        description: Human-readable description.
    """

    def decorator(fn: Callable) -> Callable:
        meta = {
            "name": name,
            "description": description,
            "_fn": fn,
        }
        _qualifiers.append(meta)
        _qualifier_registry[name] = fn
        fn.__aro_qualifier__ = meta
        return fn

    return decorator


def service(
    name: str,
    description: str = "",
) -> Callable:
    """Declare a long-running service provided by this plugin.

    Services are started when the ARO application starts and stopped on
    shutdown.

    Args:
        name: Service name.
        description: Human-readable description.
    """

    def decorator(cls: type) -> type:
        meta = {
            "name": name,
            "description": description,
        }
        _services.append(meta)
        cls.__aro_service__ = meta
        return cls

    return decorator


def system_object(
    name: str,
    description: str = "",
) -> Callable:
    """Declare an ARO system object provided by this plugin.

    System objects expose service-like state that ARO programs reference as
    ``<my-object>``.

    Args:
        name: System object name, e.g. ``"db-connection"``.
        description: Human-readable description.
    """

    def decorator(cls: type) -> type:
        meta = {
            "name": name,
            "description": description,
        }
        _system_objects.append(meta)
        cls.__aro_system_object__ = meta
        return cls

    return decorator


def on_event(event: str) -> Callable:
    """Register a function as an event handler.

    The function is called when the ARO runtime emits an event with the given
    name.

    Args:
        event: Event name, e.g. ``"UserCreated"``.
    """

    def decorator(fn: Callable) -> Callable:
        meta = {
            "event": event,
            "_fn": fn,
        }
        _event_handlers.append(meta)
        if event not in _event_registry:
            _event_registry[event] = []
        _event_registry[event].append(fn)
        fn.__aro_event_handler__ = meta
        return fn

    return decorator


def init(fn: Callable) -> Callable:
    """Mark a function as the plugin initialisation hook.

    Called once when the ARO runtime loads the plugin.
    """
    global _init_fn
    _init_fn = fn
    fn.__aro_init__ = True
    return fn


def shutdown(fn: Callable) -> Callable:
    """Mark a function as the plugin shutdown hook.

    Called once when the ARO runtime unloads the plugin.
    """
    global _shutdown_fn
    _shutdown_fn = fn
    fn.__aro_shutdown__ = True
    return fn


# ---------------------------------------------------------------------------
# Accessors used by runner.py
# ---------------------------------------------------------------------------


def get_plugin_info() -> Dict[str, Any]:
    """Return the ``aro_plugin_info`` dict assembled from registered components."""
    base = dict(_plugin_meta or {"name": "unnamed-plugin", "version": "0.0.0", "handle": ""})
    # Strip internal _fn references
    base["actions"] = [
        {k: v for k, v in a.items() if not k.startswith("_")} for a in _actions
    ]
    base["qualifiers"] = [
        {k: v for k, v in q.items() if not k.startswith("_")} for q in _qualifiers
    ]
    if _system_objects:
        base["systemObjects"] = [
            {k: v for k, v in s.items() if not k.startswith("_")} for s in _system_objects
        ]
    return base


def get_action(name: str) -> Optional[Callable]:
    """Return the action function registered under *name*, or ``None``."""
    return _action_registry.get(name)


def get_qualifier(name: str) -> Optional[Callable]:
    """Return the qualifier function registered under *name*, or ``None``."""
    return _qualifier_registry.get(name)


def get_event_handlers(event: str) -> List[Callable]:
    """Return all handlers registered for *event*."""
    return _event_registry.get(event, [])


def export_abi(module_dict: Dict[str, Any]) -> None:
    """Generate backward-compatible module-level functions for the ARO runtime.

    The ARO runtime's PythonPluginHost expects:
    - ``aro_plugin_info()`` at module level
    - ``aro_action_<name>(input_json)`` for each action
    - ``aro_plugin_qualifier(qualifier, input_json)`` if qualifiers exist

    Call this at the end of your plugin module::

        from aro_plugin_sdk.decorators import export_abi
        export_abi(globals())
    """
    import json as _json

    from .input import AROInput as _AROInput

    # aro_plugin_info
    def _aro_plugin_info():
        return get_plugin_info()

    module_dict["aro_plugin_info"] = _aro_plugin_info

    # aro_action_<name> for each registered action
    for action_meta in _actions:
        action_name = action_meta["name"]
        fn = action_meta.get("_fn")
        if fn is None:
            continue
        # Convert action name to snake_case for function name
        snake = action_name.replace("-", "_").replace(" ", "_").lower()

        def _make_action_fn(handler):
            def _action_fn(input_json):
                params = _json.loads(input_json) if isinstance(input_json, str) else input_json
                inp = _AROInput(params)
                result = handler(inp)
                return _json.dumps(result)
            return _action_fn

        module_dict[f"aro_action_{snake}"] = _make_action_fn(fn)

    # aro_plugin_qualifier if qualifiers exist
    if _qualifiers:
        def _aro_plugin_qualifier(qualifier_name, input_json):
            params = _json.loads(input_json) if isinstance(input_json, str) else input_json
            fn = get_qualifier(qualifier_name)
            if fn is None:
                return _json.dumps({"error": f"Unknown qualifier: {qualifier_name}"})
            inp = _AROInput(params)
            try:
                result = fn(inp)
                return _json.dumps({"result": result})
            except Exception as e:
                return _json.dumps({"error": str(e)})

        module_dict["aro_plugin_qualifier"] = _aro_plugin_qualifier
