"""Unit tests for the LLMClient (mock transport)."""

from __future__ import annotations

import pytest

from harness.llm.client import LLMClient
from harness.llm.exceptions import LLMConnectionError, LLMResponseError


@pytest.fixture
def client() -> LLMClient:
    return LLMClient(
        base_url="http://localhost:8080",
        model_name="test-model",
        api_key=None,
        timeout=5.0,
    )


@pytest.mark.asyncio
async def test_chat_returns_assistant_text(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello there!"}}
                ],
            },
        )
    )
    text = await client.chat([{"role": "user", "content": "Hi"}])
    assert text == "Hello there!"


@pytest.mark.asyncio
async def test_chat_includes_auth_header_when_key_set(respx_mock) -> None:
    client = LLMClient(
        base_url="http://localhost:8080",
        model_name="test-model",
        api_key="secret-abc",
    )
    route = respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    await client.chat([{"role": "user", "content": "Hi"}])
    assert "Authorization" in route.calls.last.request.headers
    assert route.calls.last.request.headers["Authorization"] == "Bearer secret-abc"
    await client.close()


@pytest.mark.asyncio
async def test_chat_omits_auth_when_api_key_is_none(respx_mock) -> None:
    client = LLMClient(
        base_url="http://localhost:8080",
        model_name="test-model",
        api_key=None,
    )
    route = respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    await client.chat([{"role": "user", "content": "Hi"}])
    assert "Authorization" not in route.calls.last.request.headers
    await client.close()


@pytest.mark.asyncio
async def test_chat_connection_error_no_traceback(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        side_effect=Exception("connection refused")
    )
    with pytest.raises(LLMConnectionError) as exc_info:
        await client.chat([{"role": "user", "content": "Hi"}])
    assert "connection" in str(exc_info.value).lower() or "Could not reach" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_chat_4xx_raises_response_error(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(401, json={"error": "bad key"})
    )
    with pytest.raises(LLMResponseError) as exc_info:
        await client.chat([{"role": "user", "content": "Hi"}])
    assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_chat_5xx_raises_response_error(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(500, text="server boom")
    )
    with pytest.raises(LLMResponseError):
        await client.chat([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_chat_handles_no_choices(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(200, json={"choices": []})
    )
    with pytest.raises(LLMResponseError):
        await client.chat([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_chat_handles_invalid_json(client: LLMClient, respx_mock) -> None:
    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        return_value=respx_mock.Response(200, text="<html>not json</html>")
    )
    with pytest.raises(LLMResponseError):
        await client.chat([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_chat_handles_timeout(client: LLMClient, respx_mock) -> None:
    import httpx

    respx_mock.post("http://localhost:8080/v1/chat/completions").mock(
        side_effect=httpx.TimeoutException("slow")
    )
    with pytest.raises(LLMConnectionError):
        await client.chat([{"role": "user", "content": "Hi"}])
