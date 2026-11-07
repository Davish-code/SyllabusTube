"""Abstract base interface for LLM client providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """Abstract interface defining the uniform contract for LLM backends."""

    @abstractmethod
    def generate_text(
        self, prompt: str, temperature: float = 0.1, max_tokens: int | None = None
    ) -> str:
        """Generate plain text from prompt."""

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate structured JSON conforming to optional schema."""
