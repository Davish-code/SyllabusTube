"""Google Gemini LLM provider implementation."""

from __future__ import annotations

from typing import Any

from syllabustube.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini models via official SDK or REST."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model = model

    def generate_text(
        self, prompt: str, temperature: float = 0.1, max_tokens: int | None = None
    ) -> str:
        """Generate text using Gemini."""
        raise NotImplementedError("Gemini API calls will be implemented in Phase 1.")

    def generate_json(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate structured JSON using Gemini."""
        raise NotImplementedError("Gemini structured output will be implemented in Phase 1.")
