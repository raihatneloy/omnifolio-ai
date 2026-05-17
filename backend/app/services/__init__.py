from app.services.llm.registry import registry as provider_registry
from app.services.llm.openrouter import OpenRouterProvider

# Register the default provider
provider_registry.register(
    key="openrouter", 
    provider=OpenRouterProvider(), 
    description="OpenRouter gateway for multi-model access"
)

__all__ = ["provider_registry", "OpenRouterProvider"]
