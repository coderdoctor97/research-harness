# Phase 2 P2.T6 config system tests
from harness.config.resolver import resolve, load_dotenv
from harness.config.templates import render
from harness.config.validation import validate, ConfigError


def test_resolve_env_var(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert resolve("${FOO}") == "bar"


def test_resolve_missing_warns():
    out = resolve("${MISSING:MY_KEY}")
    assert "MISSING:" in out


def test_render_template():
    # Template engine handles {{placeholder|default:x}}; bare {{PORT}} is left for the resolver
    assert render("http://localhost:{{PORT}}/v1") == "http://localhost:{{PORT}}/v1"
    assert render("http://localhost:{{PORT|default:8080}}/v1") == "http://localhost:8080/v1"
    assert render("/items/{{id|default:0}}").endswith("/items/0")


def test_render_default_when_missing():
    assert "8080" in render("http://localhost:{{MISSING|default:8080}}/v1")


def test_render_query_and_path():
    assert "?" in render("/search?q={{query}}")
    assert render("/items/{{id|default:0}}").endswith("/items/0")


def test_validate_valid_config():
    cfg = {
        "llm": {"base_url": "http://localhost:11434/v1", "model_name": "llama3"},
        "endpoints": [],
        "custom_endpoints": [],
    }
    v = validate(cfg)
    assert v.llm["model_name"] == "llama3"


def test_validate_invalid_raises_friendly():
    try:
        validate({"llm": "not-a-dict", "endpoints": "bad"})
    except ConfigError as exc:
        assert "Invalid config" in str(exc)
