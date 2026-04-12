"""Tests for aro_plugin_sdk.input.AROInput."""

import pytest
from aro_plugin_sdk.input import AROInput
from aro_plugin_sdk.testing import mock_input, mock_http_input


class TestStringAccessor:
    def test_string_returns_value(self):
        inp = mock_input({"name": "Alice"})
        assert inp.string("name") == "Alice"

    def test_string_missing_returns_default(self):
        inp = mock_input({})
        assert inp.string("name") == ""
        assert inp.string("name", "Bob") == "Bob"

    def test_string_coerces_int(self):
        inp = mock_input({"count": 42})
        assert inp.string("count") == "42"


class TestIntAccessor:
    def test_int_returns_value(self):
        inp = mock_input({"count": 3})
        assert inp.int("count") == 3

    def test_int_missing_returns_default(self):
        inp = mock_input({})
        assert inp.int("count") == 0
        assert inp.int("count", 99) == 99


class TestFloatAccessor:
    def test_float_returns_value(self):
        inp = mock_input({"price": 3.14})
        assert inp.float("price") == pytest.approx(3.14)

    def test_float_from_int(self):
        inp = mock_input({"price": 10})
        assert inp.float("price") == pytest.approx(10.0)


class TestBoolAccessor:
    def test_bool_true(self):
        inp = mock_input({"enabled": True})
        assert inp.bool("enabled") is True

    def test_bool_false(self):
        inp = mock_input({"enabled": False})
        assert inp.bool("enabled") is False

    def test_bool_string_true(self):
        inp = mock_input({"enabled": "true"})
        assert inp.bool("enabled") is True

    def test_bool_string_false(self):
        inp = mock_input({"enabled": "false"})
        assert inp.bool("enabled") is False

    def test_bool_missing_default(self):
        inp = mock_input({})
        assert inp.bool("enabled") is False
        assert inp.bool("enabled", True) is True


class TestArrayAccessor:
    def test_array_returns_list(self):
        inp = mock_input({"items": [1, 2, 3]})
        assert inp.array("items") == [1, 2, 3]

    def test_array_missing_returns_empty(self):
        inp = mock_input({})
        assert inp.array("items") == []


class TestDictAccessor:
    def test_dict_returns_dict(self):
        inp = mock_input({"meta": {"key": "val"}})
        assert inp.dict("meta") == {"key": "val"}

    def test_dict_missing_returns_empty(self):
        inp = mock_input({})
        assert inp.dict("meta") == {}


class TestWithFallback:
    def test_with_fallback(self):
        inp = mock_input({"_with": {"flag": True}})
        assert inp.bool("flag") is True

    def test_top_level_wins_over_with(self):
        inp = mock_input({"x": 1, "_with": {"x": 99}})
        assert inp.int("x") == 1

    def test_with_params(self):
        inp = mock_input({"_with": {"order": "desc"}})
        params = inp.with_params()
        assert params.string("order") == "desc"

    def test_empty_with_params(self):
        inp = mock_input({})
        params = inp.with_params()
        assert params.string("order") == ""


class TestDescriptors:
    def test_result_identifier(self):
        inp = mock_input({"result": {"identifier": "output", "qualifier": "uppercase"}})
        assert inp.result_identifier() == "output"
        assert inp.result_qualifier() == "uppercase"

    def test_source_identifier(self):
        inp = mock_input({"object": {"identifier": "source", "qualifier": None}})
        assert inp.source_identifier() == "source"

    def test_preposition(self):
        inp = mock_input({"preposition": "from"})
        assert inp.preposition() == "from"

    def test_missing_descriptors(self):
        inp = mock_input({})
        assert inp.result_identifier() is None
        assert inp.result_qualifier() is None
        assert inp.source_identifier() is None
        assert inp.preposition() is None


class TestContextAccessor:
    def test_context_get(self):
        inp = mock_input({"context": {"userId": "42"}})
        assert inp.context_get("userId") == "42"

    def test_context_get_missing(self):
        inp = mock_input({})
        assert inp.context_get("userId") is None

    def test_mock_http_input(self):
        inp = mock_http_input(
            path_params={"id": "42"},
            body={"name": "Alice"},
        )
        ctx = inp.context()
        assert ctx is not None
        assert ctx["pathParameters"] == {"id": "42"}
        assert ctx["body"] == {"name": "Alice"}


class TestFromJson:
    def test_from_json_string(self):
        inp = AROInput.from_json('{"name": "Alice"}')
        assert inp.string("name") == "Alice"
