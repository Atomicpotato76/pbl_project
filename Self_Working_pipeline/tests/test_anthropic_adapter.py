from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from services.adapters.anthropic_adapter import (
    ANTHROPIC_WEB_FETCH_TOOL_TYPE,
    ANTHROPIC_WEB_SEARCH_TOOL_TYPE,
    AnthropicJsonAdapter,
)


class TinyModel(BaseModel):
    value: str


class EnvelopeModel(BaseModel):
    result: TinyModel


class DummyRateLimitError(Exception):
    status_code = 429


def _message(*, text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
    )


def _make_adapter(
    responses: list[SimpleNamespace],
    *,
    web_search_enabled: bool = False,
    web_fetch_enabled: bool = False,
) -> tuple[AnthropicJsonAdapter, list[dict]]:
    calls: list[dict] = []

    class DummyClient:
        def __init__(self) -> None:
            self.messages = SimpleNamespace(create=self.create)

        def create(self, **kwargs):
            calls.append(kwargs)
            response = responses[len(calls) - 1]
            if isinstance(response, Exception):
                raise response
            return response

    adapter = AnthropicJsonAdapter(
        api_key="test-key",
        model="test-model",
        thinking_enabled=True,
        max_output_tokens=5000,
        web_search_enabled=web_search_enabled,
        web_fetch_enabled=web_fetch_enabled,
    )
    adapter.client = DummyClient()
    return adapter, calls


def test_generate_structured_retries_without_thinking_when_truncated() -> None:
    adapter, calls = _make_adapter(
        [
            _message(text='{"value": "truncated', stop_reason="max_tokens"),
            _message(text='{"value": "ok"}'),
        ]
    )

    result = adapter.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=TinyModel,
    )

    assert result.value == "ok"
    assert len(calls) == 2
    assert "thinking" in calls[0]
    assert "thinking" not in calls[1]
    assert calls[1]["max_tokens"] == 12000


def test_generate_structured_retries_on_validation_error() -> None:
    adapter, calls = _make_adapter(
        [
            _message(text='{"value": "no-envelope"}'),
            _message(text='{"result": {"value": "wrapped"}}'),
        ]
    )

    envelope = adapter.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=EnvelopeModel,
    )

    assert envelope.result.value == "wrapped"
    assert len(calls) == 2
    assert "schema validation" in calls[1]["system"]


def test_generate_structured_extracts_json_from_prose() -> None:
    prose = "Here is the JSON you requested:\n```json\n{\"value\": \"clean\"}\n```\nThanks."
    adapter, _ = _make_adapter([_message(text=prose)])

    result = adapter.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=TinyModel,
    )

    assert result.value == "clean"


def test_generate_structured_raises_runtime_error_after_retry_fails() -> None:
    adapter, calls = _make_adapter(
        [
            _message(text="totally not json"),
            _message(text="still not json"),
        ]
    )

    with pytest.raises(RuntimeError) as excinfo:
        adapter.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=TinyModel,
        )

    assert "after retry" in str(excinfo.value)
    assert len(calls) == 2


def test_generate_structured_retries_after_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter, calls = _make_adapter(
        [
            DummyRateLimitError("429 rate limit"),
            _message(text='{"value": "ok"}'),
        ]
    )
    sleeps: list[int] = []
    monkeypatch.setattr("services.adapters.anthropic_adapter.time.sleep", sleeps.append)

    result = adapter.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=TinyModel,
    )

    assert result.value == "ok"
    assert len(calls) == 2
    assert sleeps == [15]


def test_build_request_kwargs_includes_server_tools_when_enabled() -> None:
    adapter, _ = _make_adapter(
        [_message(text='{"value": "ok"}')],
        web_search_enabled=True,
        web_fetch_enabled=True,
    )

    request_kwargs = adapter._build_request_kwargs(
        system_prompt="system",
        user_prompt="user",
        schema="{}",
        thinking_enabled=True,
        max_tokens=5000,
    )

    assert request_kwargs["tools"] == [
        {"type": ANTHROPIC_WEB_SEARCH_TOOL_TYPE, "name": "web_search", "max_uses": 4},
        {"type": ANTHROPIC_WEB_FETCH_TOOL_TYPE, "name": "web_fetch", "max_uses": 2},
    ]
    assert "web_search" in request_kwargs["system"]
    assert "web_fetch" in request_kwargs["system"]
