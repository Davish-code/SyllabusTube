"""Local Ollama LLM provider implementation."""

from __future__ import annotations

from typing import Any

from syllabustube.llm.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Client for local open models running on Ollama."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.model = model

    def generate_text(
        self, prompt: str, temperature: float = 0.1, max_tokens: int | None = None
    ) -> str:
        """Generate text using local Ollama model."""
        raise NotImplementedError("Ollama calls will be implemented in Phase 1.")

    def generate_json(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate structured JSON using Ollama."""
        raise NotImplementedError("Ollama structured output will be implemented in Phase 1.")
