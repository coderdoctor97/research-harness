# Tests for LLM client — chat, streaming, and list_models
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError


def _make_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


class TestLLMClient:
    def test_chat_basic(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "llama3"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()

        mock_resp = _make_response(json_data={
            "choices": [{"message": {"content": "Hello there!"}}]
        })
        client.client.post.return_value = mock_resp

        result = client.chat("hi")
        assert result == "Hello there!"
        client.client.post.assert_called_once()
        call_args = client.client.post.call_args
        body = call_args.kwargs.get("json") or call_args.args[1]
        assert body["model"] == "llama3"
        assert body["messages"][0]["content"] == "hi"
        assert body["stream"] is False

    def test_chat_includes_max_tokens_when_set(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "llama3"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.max_tokens = 2048
        client.client = MagicMock()
        client.client.post.return_value = _make_response(json_data={
            "choices": [{"message": {"content": "ok"}}]
        })
        client.chat("hi")
        body = client.client.post.call_args.kwargs.get("json")
        assert body["max_tokens"] == 2048

    def test_chat_omits_max_tokens_when_unset(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "llama3"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()
        client.client.post.return_value = _make_response(json_data={
            "choices": [{"message": {"content": "ok"}}]
        })
        client.chat("hi")
        body = client.client.post.call_args.kwargs.get("json")
        assert "max_tokens" not in body

    def test_chat_empty_choices(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()
        client.client.post.return_value = _make_response(json_data={"choices": []})

        with pytest.raises(LLMResponseError, match="Empty choices"):
            client.chat("test")

    def test_chat_connection_error(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()
        client.client.post.side_effect = httpx.ConnectError("refused")

        with pytest.raises(LLMConnectionError):
            client.chat("test")

    def test_chat_http_error(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()
        resp = _make_response(status_code=500)
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=resp
        )
        client.client.post.return_value = resp

        with pytest.raises(LLMResponseError, match="HTTP 500"):
            client.chat("test")

    def test_list_models(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()

        mock_resp = _make_response(json_data={
            "data": [
                {"id": "llama3", "owned_by": "meta"},
                {"id": "mistral", "owned_by": "mistralai"},
            ]
        })
        client.client.get.return_value = mock_resp

        models = client.list_models()
        assert len(models) == 2
        assert models[0]["id"] == "llama3"
        assert models[0]["name"] == "llama3"
        assert models[0]["owned_by"] == "meta"
        assert models[1]["id"] == "mistral"
        client.client.get.assert_called_once()

    def test_list_models_empty(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()
        client.client.get.return_value = _make_response(json_data={"data": []})

        models = client.list_models()
        assert models == []

    def test_stream_chat(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0
        client.client = MagicMock()

        sse_lines = (
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n'
            'data: {"choices":[{"delta":{"content":" world"}}]}\n'
            "data: [DONE]\n"
        )
        mock_resp = _make_response(text=sse_lines)
        client.client.post.return_value = mock_resp

        chunks = list(client.stream_chat("hi"))
        assert "".join(chunks) == "Hello world"
        assert len(chunks) == 2

    def test_headers_with_api_key(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "MY_KEY"
        client.timeout = 30.0

        import os
        with patch.dict(os.environ, {"MY_KEY": "secret123"}):
            headers = client._headers()
        assert headers["Authorization"] == "Bearer secret123"
        assert headers["Content-Type"] == "application/json"

    def test_headers_no_api_key(self):
        client = LLMClient.__new__(LLMClient)
        client.base_url = "http://localhost:11434/v1"
        client.model_name = "test"
        client.api_key_env = "none"
        client.timeout = 30.0

        headers = client._headers()
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"