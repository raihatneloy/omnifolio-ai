"""
ProviderRegistry — manages all registered LLM providers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import LLMError, LLMProvider


class RegistryError(LLMError):
    """Raised when provider registration or lookup fails."""


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    provider: LLMProvider
    enabled: bool = True
    description: str = ""


class ProviderRegistry:
    """Central registry for all LLM providers.

    Usage
    -----
    >>> from app.services.llm import registry, registry_status
    >>> from app.services.llm.openrouter import OpenRouterProvider
    >>>
    >>> registry.register("openrouter", OpenRouterProvider(api_key="sk-..."))
    >>> provider = registry.get("openrouter")
    >>> resp = await provider.complete("Hello")
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderConfig] = {}

    # ── Registration ───────────────────────────────────────────

    def register(
        self,
        key: str,
        provider: LLMProvider,
        *,
        enabled: bool = True,
        description: str = "",
    ) -> None:
        key = key.lower().strip()
        if not key:
            raise RegistryError("Provider key must be non-empty")
        self._providers[key] = ProviderConfig(
            provider=provider,
            enabled=enabled,
            description=description,
        )

    def unregister(self, key: str) -> bool:
        key = key.lower().strip()
        return self._providers.pop(key, None) is not None

    # ── Lookup ─────────────────────────────────────────────────

    def get(
        self,
        key: str,
        *,
        include_disabled: bool = False,
    ) -> LLMProvider:
        key = key.lower().strip()
        config = self._providers.get(key)
        if config is None:
            raise RegistryError(f"Provider '{key}' is not registered")
        if not config.enabled and not include_disabled:
            raise RegistryError(
                f"Provider '{key}' is registered but disabled. "
                "Set enabled=True to activate."
            )
        return config.provider

    def is_registered(self, key: str) -> bool:
        return key.lower().strip() in self._providers

    def is_enabled(self, key: str) -> bool:
        key = key.lower().strip()
        config = self._providers.get(key)
        return config is not None and config.enabled

    # ── Defaults ───────────────────────────────────────────────

    def get_default(self) -> LLMProvider:
        enabled = [c.provider for c in self._providers.values() if c.enabled]
        if not enabled:
            raise RegistryError(
                "No enabled LLM providers registered. "
                "Add at least one provider via registry.register(...)."
            )
        return enabled[0]

    def default_key(self) -> str:
        for key, config in self._providers.items():
            if config.enabled:
                return key
        raise RegistryError("No enabled providers")

    def registry_status(self) -> dict[str, dict]:
        """Return a dict of all registered providers and their status."""
        return {
            key: {
                "name": config.provider.name,
                "default_model": config.provider.default_model,
                "enabled": config.enabled,
                "description": config.description,
            }
            for key, config in self._providers.items()
        }

    # ── Introspection ──────────────────────────────────────────


    def list_enabled(self) -> list[str]:
        return [k for k, c in self._providers.items() if c.enabled]


# ── Global singleton ──────────────────────────────────────────────────────────

registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Return the global ProviderRegistry instance."""
    return registry

# ── Convenience re-exports ────────────────────────────────────────────────────

from .base import (
    AuthenticationError,
    LLMError,
    LLMResponse,
    LLMProvider,
    ModelNotFoundError,
    RateLimitError,
)

__all__ = [
    "registry",
    "get_registry",
    "registry_status",
    "ProviderRegistry",
    "RegistryError",
    "LLMProvider",
    "LLMResponse",
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
]