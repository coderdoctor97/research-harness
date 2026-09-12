# P7.T5 — Custom endpoint tests: dynamic tools, schema inference, fallback, hot-reload
from __future__ import annotations

import pytest
from harness.config.models import CustomEndpointDef, EndpointDef
from harness.registry.dynamic import build_dynamic_tool, _infer_schema
from harness.registry.tool import ToolResult
from harness.registry.validation_extras import validate_custom_endpoint, CustomEndpointError, group_by_mapping
from harness.registry.fallback import execute_with_fallback
from harness.registry.index import ToolRegistry


def test_dynamic_tool_basic():
    ep = CustomEndpointDef(
        name="my_search",
        description="Search something",
        endpoint=EndpointDef(url="https://api.example.com/search?q={{query}}"),
    )
    tool = build_dynamic_tool(ep)
    assert tool is not None
    assert tool.name == "my_search"
    schema = tool.schema()
    assert schema["function"]["name"] == "my_search"


def test_dynamic_tool_schema_inference():
    ep = CustomEndpointDef(
        name="calc",
        endpoint=EndpointDef(url="https://api.example.com/{{n|default:0}}"),
        parameters={"body_template": '{"x": {{x|default:1}}, "y": {{y|default:null}}'},
    )
    schema = _infer_schema(ep)
    props = schema["properties"]
    assert "n" in props
    assert "x" in props
    assert "y" in props
    assert schema["required"] == ["n", "x"]  # y has default:null


def test_dynamic_tool_no_url_returns_none():
    ep = CustomEndpointDef(name="bad", endpoint=EndpointDef(url=""))
    tool = build_dynamic_tool(ep)
    assert tool is None


def test_validate_custom_endpoint_ok():
    ep = CustomEndpointDef(
        name="ok",
        endpoint=EndpointDef(url="https://api.example.com"),
    )
    validate_custom_endpoint(ep)  # should not raise


def test_validate_custom_endpoint_no_name():
    ep = CustomEndpointDef(name="", endpoint=EndpointDef(url="https://api.example.com"))
    with pytest.raises(CustomEndpointError, match="name"):
        validate_custom_endpoint(ep)


def test_validate_custom_endpoint_no_url():
    ep = CustomEndpointDef(name="x", endpoint=EndpointDef(url=""))
    with pytest.raises(CustomEndpointError, match="url"):
        validate_custom_endpoint(ep)


def test_group_by_mapping():
    eps = [
        CustomEndpointDef(name="tool_a", tool_mapping="shared", endpoint=EndpointDef(url="https://a"), enabled=True),
        CustomEndpointDef(name="tool_b", tool_mapping="shared", endpoint=EndpointDef(url="https://b"), enabled=True),
        CustomEndpointDef(name="tool_c", endpoint=EndpointDef(url="https://c"), enabled=False),
    ]
    groups = group_by_mapping(eps)
    assert "shared" in groups
    assert len(groups["shared"]) == 2


def test_fallback_on_primary_failure():
    from unittest.mock import patch, MagicMock
    primary = CustomEndpointDef(name="f1", endpoint=EndpointDef(url="http://fail1"), enabled=True)
    secondary = CustomEndpointDef(name="f2", endpoint=EndpointDef(url="http://fail2"), enabled=True)
    fail_result = ToolResult(ok=False, error="HTTP 500")
    with patch("harness.registry.dynamic.build_dynamic_tool") as mock_build:
        t1 = build_dynamic_tool(primary)
        t2 = build_dynamic_tool(secondary)
        mock_build.side_effect = [t1, t2]
        with patch.object(t1, "run", return_value=fail_result):
            with patch.object(t2, "run", return_value=ToolResult(ok=True, data={"result": "ok"})):
                r = execute_with_fallback([primary, secondary], {})
    assert r.ok
    assert r.data["result"] == "ok"


def test_registry_add_remove_dynamic_tool():
    reg = ToolRegistry()
    ep = CustomEndpointDef(
        name="dynamic_tool",
        description="A dynamic tool",
        endpoint=EndpointDef(url="https://api.example.com/items?q={{query}}"),
    )
    tool = build_dynamic_tool(ep)
    assert tool is not None
    reg.register(tool)
    assert reg.primary("dynamic_tool") is tool
    schemas = reg.list_schemas()
    assert any(s["function"]["name"] == "dynamic_tool" for s in schemas)
