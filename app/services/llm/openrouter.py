"""
OpenRouter provider — calls any model via OpenRouter's OpenAI-compatible API.

OpenRouter (openrouter.ai) acts as a unified gateway to 100+ LLMs using the
standard OpenAI client library. No provider-specific SDK needed.
"""

from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import get_settings
from .base import (
    AuthenticationError,
    LLMError,
    LLMResponse,
    LLMProvider,
    ModelNotFoundError,
    RateLimitError,
)


class OpenRouterProvider(LLMProvider):
    """OpenRouter-backed LLM provider.

    Parameters
    ----------
    api_key:
        OpenRouter API key. Falls back to ``OPENROUTER_API_KEY`` env var
        if not provided.
    base_url:
        OpenRouter API base URL. Defaults to ``https://openrouter.ai/api/v1``.
    timeout:
        Request timeout in seconds. Defaults to 60.
    """

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def default_model(self) -> str:
        return "openai/gpt-4o-mini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def api_key(self) -> str:
        if self._api_key:
            return self._api_key
        settings = get_settings()
        key = getattr(settings, "openrouter_api_key", None)  # type: ignore[attr-defined]
        if not key:
            raise AuthenticationError(
                "OpenRouter API key not set. "
                "Pass it to OpenRouterProvider(api_key=...) or "
                "set OPENROUTER_API_KEY in your .env file."
            )
        return key

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://omnifolio.ai",
                "X-Title": "OmniFolio AI",
            },
            timeout=httpx.Timeout(self._timeout),
        )

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a chat-style prompt via OpenRouter.

        Uses the ``/chat/completions`` endpoint (OpenAI-compatible).
        The *prompt* is wrapped as a single user message.
        """
        model = model or self.default_model

        async with self._client() as client:
            try:
                response = await client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
            except httpx.TimeoutException as exc:
                raise RateLimitError(
                    f"OpenRouter request timed out after {self._timeout}s"
                ) from exc
            except httpx.RequestError as exc:
                raise LLMError(f"OpenRouter request failed: {exc}")

            data = response.json()

            if response.status_code in (401, 403):
                raise AuthenticationError(
                    data.get("error", {}).get("message", "Invalid API key or unauthorized")
                )
            if response.status_code == 429:
                raise RateLimitError(
                    data.get("error", {}).get("message", "Rate limit exceeded")
                )
            if response.status_code == 404 or (
                data.get("error", {}).get("code") == "model_not_found"
            ):
                raise ModelNotFoundError(
                    f"Model '{model}' not found on OpenRouter"
                )

            if response.status_code != 200:
                raise LLMError(
                    f"OpenRouter API error {response.status_code}: "
                    f"{data.get('error')}"
                )

            choices = data.get("choices", [])
            if not choices:
                raise LLMError("OpenRouter returned no choices")

            message = choices[0].get("message", {})
            content = message.get("content", "")
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")

            return LLMResponse(
                content=content,
                model=data.get("model", model),
                tokens_used=tokens_used,
                raw=data,
            )