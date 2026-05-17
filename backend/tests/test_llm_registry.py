"""
Tests for the LLM Provider Registry (Chunk 1.1).
"""

from __future__ import annotations

import asyncio

import pytest

from app.services.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
)
from app.services.llm.registry import (
    ProviderRegistry,
    RegistryError,
    get_registry,
)
from app.services.llm import registry as llm_registry


# ── Test helpers ──────────────────────────────────────────────────────────────


class DummyProvider(LLMProvider):
    """Minimal concrete provider for testing."""

    name: str = "dummy"
    default_model: str = "dummy/test"

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        return LLMResponse(content="dummy response", model=self.default_model)


# ── ProviderRegistry ──────────────────────────────────────────────────────────


class TestProviderRegistry:
    def setup_method(self) -> None:
        self.reg = ProviderRegistry()

    # Registration

    def test_register_one(self) -> None:
        p = DummyProvider()
        self.reg.register("dummy", p)
        assert self.reg.is_registered("dummy")
        assert self.reg.get("dummy") is p

    def test_register_multiple(self) -> None:
        p1, p2 = DummyProvider(), DummyProvider()
        self.reg.register("one", p1)
        self.reg.register("two", p2)
        assert self.reg.get("one") is p1
        assert self.reg.get("two") is p2

    def test_register_replaces(self) -> None:
        p1, p2 = DummyProvider(), DummyProvider()
        self.reg.register("key", p1)
        self.reg.register("key", p2)
        assert self.reg.get("key") is p2

    def test_register_key_normalised(self) -> None:
        p = DummyProvider()
        self.reg.register("  OPENROUTER  ", p)
        assert self.reg.get("openrouter") is p

    def test_register_empty_key_raises(self) -> None:
        with pytest.raises(RegistryError, match="non-empty"):
            self.reg.register("", DummyProvider())

    def test_register_whitespace_key_raises(self) -> None:
        with pytest.raises(RegistryError, match="non-empty"):
            self.reg.register("   ", DummyProvider())

    # Lookup

    def test_get_known(self) -> None:
        p = DummyProvider()
        self.reg.register("test", p)
        assert self.reg.get("test") is p

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(RegistryError, match="not registered"):
            self.reg.get("nobody")

    def test_get_disabled_raises_by_default(self) -> None:
        p = DummyProvider()
        self.reg.register("off", p, enabled=False)
        with pytest.raises(RegistryError, match="disabled"):
            self.reg.get("off")

    def test_get_disabled_allowed_with_flag(self) -> None:
        p = DummyProvider()
        self.reg.register("off", p, enabled=False)
        assert self.reg.get("off", include_disabled=True) is p

    # Unregister

    def test_unregister_exists(self) -> None:
        p = DummyProvider()
        self.reg.register("bye", p)
        assert self.reg.unregister("bye") is True
        assert not self.reg.is_registered("bye")

    def test_unregister_missing(self) -> None:
        assert self.reg.unregister("ghost") is False

    # Default provider

    def test_get_default_single(self) -> None:
        p = DummyProvider()
        self.reg.register("only", p)
        assert self.reg.get_default() is p

    def test_get_default_first_enabled(self) -> None:
        p1, p2 = DummyProvider(), DummyProvider()
        self.reg.register("first", p1, enabled=False)
        self.reg.register("second", p2, enabled=True)
        assert self.reg.get_default() is p2

    def test_get_default_no_providers(self) -> None:
        with pytest.raises(RegistryError, match="No enabled"):
            self.reg.get_default()

    def test_default_key(self) -> None:
        p = DummyProvider()
        self.reg.register("myprovider", p)
        assert self.reg.default_key() == "myprovider"

    def test_default_key_none_enabled(self) -> None:
        p = DummyProvider()
        self.reg.register("disabled", p, enabled=False)
        with pytest.raises(RegistryError, match="No enabled"):
            self.reg.default_key()

    # Introspection

    def test_list_keys(self) -> None:
        self.reg.register("a", DummyProvider())
        self.reg.register("b", DummyProvider(), enabled=False)
        assert set(self.reg.list_keys()) == {"a", "b"}

    def test_list_enabled(self) -> None:
        self.reg.register("yes", DummyProvider(), enabled=True)
        self.reg.register("no", DummyProvider(), enabled=False)
        assert self.reg.list_enabled() == ["yes"]

    def test_is_enabled(self) -> None:
        self.reg.register("on", DummyProvider(), enabled=True)
        self.reg.register("off", DummyProvider(), enabled=False)
        assert self.reg.is_enabled("on") is True
        assert self.reg.is_enabled("off") is False
        assert self.reg.is_enabled("ghost") is False


# ── LLMResponse dataclass ──────────────────────────────────────────────────────


class TestLLMResponse:
    def test_basic(self) -> None:
        r = LLMResponse(content="hello", model="gpt-4")
        assert r.content == "hello"
        assert r.model == "gpt-4"
        assert r.tokens_used is None
        assert r.raw is None

    def test_full(self) -> None:
        raw = {"id": "chatcmpl-1", "usage": {"total_tokens": 42}}
        r = LLMResponse(
            content="hello",
            model="gpt-4",
            tokens_used=42,
            raw=raw,
        )
        assert r.tokens_used == 42
        assert r.raw == raw


# ── Error hierarchy ───────────────────────────────────────────────────────────


class TestErrorHierarchy:
    def test_llm_error_catches_all(self) -> None:
        errors = [
            AuthenticationError("auth"),
            RateLimitError("rate"),
            ModelNotFoundError("model"),
        ]
        for err in errors:
            assert isinstance(err, LLMError)

    def test_auth_error_message(self) -> None:
        err = AuthenticationError("bad key")
        assert str(err) == "bad key"


# ── map_headers default implementation ───────────────────────────────────────
# Note: map_headers is synchronous (not async) — it calls self.complete(...)
# which is async, so callers use await provider.map_headers(...)


class TestMapHeaders:
    def test_calls_complete_with_headers_and_rows(self) -> None:
        p = DummyProvider()
        captured: dict = {}

        async def spy_complete(prompt, **kw):
            captured["prompt"] = prompt
            return LLMResponse(content="{}", model=p.default_model)

        p.complete = spy_complete  # type: ignore[assignment]

        resp = p.map_headers(
            headers=["Symbol", "Shares", "Price"],
            sample_rows=[["AAPL", "100", "150.00"]],
        )

        # map_headers is sync — complete() returns a coroutine, so we await it
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(resp)

        prompt = captured["prompt"]
        assert '"Symbol"' in prompt
        assert '"Shares"' in prompt
        assert "AAPL" in prompt
        assert "ticker" in prompt
        assert "quantity" in prompt

    def test_map_headers_returns_coroutine(self) -> None:
        p = DummyProvider()

        async def mock_complete(prompt, **kw):
            return LLMResponse(
                content='{"ticker": "Symbol"}', model="dummy/test"
            )

        p.complete = mock_complete  # type: ignore[assignment]

        resp = p.map_headers(
            headers=["Symbol"],
            sample_rows=[["AAPL"]],
        )

        assert asyncio.iscoroutine(resp)

        async def check():
            result = await resp
            assert isinstance(result, LLMResponse)
            assert result.model == "dummy/test"

        asyncio.get_event_loop().run_until_complete(check())


# ── Global registry singleton ──────────────────────────────────────────────────


class TestGlobalRegistry:
    def test_get_registry_returns_singleton(self) -> None:
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2  # same object

    def test_global_is_provider_registry(self) -> None:
        r = get_registry()
        assert isinstance(r, ProviderRegistry)

    def test_can_register_on_global(self) -> None:
        p = DummyProvider()
        llm_registry.register("test_global", p)
        assert llm_registry.get("test_global") is p
        llm_registry.unregister("test_global")  # clean up