"""
LLM Provider Base — abstract interface all LLM backends must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMResponse:
    """Plain response from an LLM call."""

    content: str
    model: str
    tokens_used: Optional[int] = None
    raw: Optional[dict] = None  # provider-specific raw response


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Implementations must be registered with ProviderRegistry to be usable.

    Example
    -------
    >>> registry = ProviderRegistry()
    >>> registry.register("openrouter", OpenRouterProvider(api_key="sk-..."))
    >>> provider = registry.get("openrouter")
    >>> resp = provider.complete("Hello, world!")
    >>> print(resp.content)
    """

    name: str  # human-readable identifier, e.g. "openrouter"
    default_model: str  # default model for this provider

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a text prompt and return the LLM's response.

        Parameters
        ----------
        prompt:
            The full prompt to send. For OmniFolio this will be a structured
            instruction + few-shot examples for the semantic mapper.
        model:
            Override the default model. None = use provider's default.
        temperature:
            Sampling temperature. Lower = more deterministic (good for mapping).
        max_tokens:
            Maximum tokens in the response. Must be > 0.

        Returns
        -------
        LLMResponse
            The model's response content and metadata.

        Raises
        ------
        LLMError
            Subclass-specific errors (auth failure, rate limit, etc.).
        """
        ...

    def map_headers(
        self,
        headers: list[str],
        sample_rows: list[list[str]],
    ) -> LLMResponse:
        """Map raw file headers to OmniFolio universal schema fields.

        Default implementation calls :meth:`complete` with a structured prompt.
        Providers can override to use a different prompt strategy.

        Parameters
        ----------
        headers:
            Column headers from the uploaded file, e.g.
            ``["Symbol", "Shares", "Cost Basis", "Date Acquired"]``.
        sample_rows:
            Up to 5 sample rows from the file to give the LLM context.
        """
        rows_str = "\n".join(
            " | ".join(cell for cell in row) for row in sample_rows
        )
        headers_str = ", ".join(f'"{h}"' for h in headers)

        prompt = (
            'You are a financial data mapping assistant. '
            'Given the column headers of a portfolio CSV/PDF and sample rows, '
            'output ONLY valid JSON mapping each source column to the nearest '
            'OmniFolio schema field.\n\n'
            "Allowed schema fields: ticker, quantity, cost_basis, txn_type, "
            "txn_date, price, fees, asset_type, account_id, notes\n\n"
            f"Source headers: [{headers_str}]\n\n"
            f"Sample rows:\n{rows_str}\n\n"
            "Respond ONLY with valid JSON in this exact shape "
            '(no markdown, no explanation):\n'
            '{"ticker": "Source Column Name", "quantity": "...", ...}\n'
            "Use null for columns that do not map to any schema field."
        )

        return self.complete(prompt, temperature=0.2, max_tokens=512)


class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    pass


class AuthenticationError(LLMError):
    """Raised when the API key or token is invalid or missing."""

    pass


class RateLimitError(LLMError):
    """Raised when the provider's rate limit has been exceeded."""

    pass


class ModelNotFoundError(LLMError):
    """Raised when the requested model is not available for this provider."""

    pass