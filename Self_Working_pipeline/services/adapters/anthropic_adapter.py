from __future__ import annotations

import json
import time
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

from core.serialization import parse_json_model
from core.settings import get_settings
from services.adapters.base import JsonModelAdapter

ANTHROPIC_WEB_SEARCH_TOOL_TYPE = "web_search_20260209"
ANTHROPIC_WEB_FETCH_TOOL_TYPE = "web_fetch_20250910"
RATE_LIMIT_RETRY_DELAYS_SECONDS = (15, 30, 60)


class AnthropicJsonAdapter(JsonModelAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        thinking_enabled: bool = False,
        thinking_type: str = "adaptive",
        thinking_budget_tokens: int = 0,
        max_output_tokens: int = 8000,
        web_search_enabled: bool | None = None,
        web_search_max_uses: int | None = None,
        web_fetch_enabled: bool | None = None,
        web_fetch_max_uses: int | None = None,
    ) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.thinking_enabled = thinking_enabled
        self.thinking_type = thinking_type
        self.thinking_budget_tokens = thinking_budget_tokens
        self.max_output_tokens = max_output_tokens
        settings = get_settings()
        self.web_search_enabled = (
            settings.anthropic_web_search_enabled if web_search_enabled is None else web_search_enabled
        )
        self.web_search_max_uses = (
            settings.anthropic_web_search_max_uses if web_search_max_uses is None else web_search_max_uses
        )
        self.web_fetch_enabled = (
            settings.anthropic_web_fetch_enabled if web_fetch_enabled is None else web_fetch_enabled
        )
        self.web_fetch_max_uses = (
            settings.anthropic_web_fetch_max_uses if web_fetch_max_uses is None else web_fetch_max_uses
        )

    def _build_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        if self.web_search_enabled:
            tools.append(
                {
                    "type": ANTHROPIC_WEB_SEARCH_TOOL_TYPE,
                    "name": "web_search",
                    "max_uses": max(self.web_search_max_uses, 1),
                }
            )
        if self.web_fetch_enabled:
            tools.append(
                {
                    "type": ANTHROPIC_WEB_FETCH_TOOL_TYPE,
                    "name": "web_fetch",
                    "max_uses": max(self.web_fetch_max_uses, 1),
                }
            )
        return tools

    def _build_tool_guidance(self) -> str:
        notes: list[str] = []
        if self.web_search_enabled:
            notes.append(
                "- Use `web_search` for independent external verification, current-source checks, and open-web evidence gathering, but do not treat search snippets alone as sufficient support for a high-confidence claim."
            )
        if self.web_fetch_enabled:
            notes.append(
                "- Use `web_fetch` for URLs supplied by the user or surfaced by prior search results when deeper inspection is needed so evidence can be grounded in inspected source content rather than snippet text."
            )
        if not notes:
            return ""
        return "Server tool responsibilities:\n" + "\n".join(notes)

    def _build_request_kwargs(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: str,
        thinking_enabled: bool,
        max_tokens: int,
    ) -> dict[str, Any]:
        tool_guidance = self._build_tool_guidance()
        combined_system = system_prompt
        if tool_guidance:
            combined_system = f"{system_prompt}\n\n{tool_guidance}"

        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": (
                f"{combined_system}\n"
                "Return only valid JSON that matches the schema.\n"
                f"JSON Schema:\n{schema}"
            ),
            "messages": [{"role": "user", "content": user_prompt}],
        }
        tools = self._build_tools()
        if tools:
            request_kwargs["tools"] = tools
        if thinking_enabled:
            thinking = {"type": self.thinking_type}
            if self.thinking_type != "adaptive":
                thinking["budget_tokens"] = self.thinking_budget_tokens
            request_kwargs["thinking"] = thinking
        return request_kwargs

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        schema = json.dumps(response_model.model_json_schema(), indent=2)
        request_kwargs = self._build_request_kwargs(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            thinking_enabled=self.thinking_enabled,
            max_tokens=self.max_output_tokens,
        )
        message = self._create_message_with_retry(**request_kwargs)
        text_parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
        raw_text = "\n".join(text_parts)
        try:
            return parse_json_model(raw_text, response_model)
        except (json.JSONDecodeError, ValidationError) as primary_error:
            stop_reason = getattr(message, "stop_reason", None)
            retry_kwargs = self._build_request_kwargs(
                system_prompt=self._reinforce_schema_prompt(system_prompt, primary_error),
                user_prompt=user_prompt,
                schema=schema,
                thinking_enabled=False,
                max_tokens=max(self.max_output_tokens, 12000),
            )
            try:
                retry_message = self._create_message_with_retry(**retry_kwargs)
            except Exception:
                raise primary_error
            retry_text_parts = [
                block.text for block in retry_message.content if getattr(block, "type", "") == "text"
            ]
            retry_raw = "\n".join(retry_text_parts)
            try:
                return parse_json_model(retry_raw, response_model)
            except (json.JSONDecodeError, ValidationError) as retry_error:
                raise RuntimeError(
                    "Anthropic adapter could not produce schema-valid JSON after retry. "
                    f"stop_reason={stop_reason!r}. "
                    f"primary_error={type(primary_error).__name__}: {primary_error}. "
                    f"retry_error={type(retry_error).__name__}: {retry_error}. "
                    f"raw_preview={retry_raw[:400]!r}"
                ) from retry_error

    def _create_message_with_retry(self, **request_kwargs: Any):
        for attempt, delay_seconds in enumerate((0, *RATE_LIMIT_RETRY_DELAYS_SECONDS)):
            if delay_seconds:
                time.sleep(delay_seconds)
            try:
                return self.client.messages.create(**request_kwargs)
            except Exception as exc:
                if not self._is_rate_limit_error(exc) or attempt == len(RATE_LIMIT_RETRY_DELAYS_SECONDS):
                    raise
        raise RuntimeError("Anthropic adapter exhausted rate-limit retries without returning a response.")

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        if getattr(exc, "status_code", None) == 429:
            return True
        if type(exc).__name__ == "RateLimitError":
            return True
        message = str(exc).lower()
        return "rate limit" in message and "429" in message

    @staticmethod
    def _reinforce_schema_prompt(system_prompt: str, error: Exception) -> str:
        hint = (
            "Previous attempt failed schema validation. "
            "Return ONLY a single JSON object that conforms to the schema above. "
            "Do not include prose, markdown fences, or extra top-level keys. "
            "If the schema has an envelope wrapper (e.g. {\"report\": {...}} or {\"result\": {...}}), "
            "you MUST include that wrapper."
        )
        return f"{system_prompt}\n\n{hint}\nLast error: {type(error).__name__}: {str(error)[:240]}"
