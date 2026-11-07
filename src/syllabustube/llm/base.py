"""Abstract base interface for LLM client providers."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from syllabustube.exceptions import SyllabusTubeError
from syllabustube.utils.retry import retry_with_backoff

logger = logging.getLogger("syllabustube.llm")


class LLMError(SyllabusTubeError):
    """Base error for LLM interactions."""


class LLMJSONError(LLMError):
    """Raised when LLM response cannot be parsed as valid JSON."""


def extract_json_string(text: str) -> str:
    """Strip markdown code fences and isolate the JSON object/array string."""
    s = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    # If extra conversational text exists around JSON, locate boundaries
    start_bracket = s.find("[")
    start_brace = s.find("{")

    if start_bracket == -1 and start_brace == -1:
        return s

    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = s.rfind("}")
        if end_brace != -1 and end_brace > start_brace:
            return s[start_brace : end_brace + 1]
    elif start_bracket != -1:
        end_bracket = s.rfind("]")
        if end_bracket != -1 and end_bracket > start_bracket:
            return s[start_bracket : end_bracket + 1]

    return s


class LLMClient(ABC):
    """Abstract interface defining the uniform contract for LLM backends."""

    supports_vision: bool = False

    @abstractmethod
    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        """Provider-specific implementation for generating plain text."""

    @abstractmethod
    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        """Provider-specific implementation returning JSON text (or structured dict serialized to str)."""

    @retry_with_backoff(max_retries=3, initial_delay=1.0, jitter=True)
    def generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        """Generate plain text from prompt with retries on transient errors."""
        if images and not self.supports_vision:
            raise LLMError(f"{self.__class__.__name__} does not support vision/image inputs.")

        start_time = time.perf_counter()
        result = self._raw_generate_text(prompt=prompt, system=system, images=images)
        elapsed = time.perf_counter() - start_time
        logger.debug(
            "LLM generate_text completed in %.3fs (prompt_len=%d, images=%d)",
            elapsed,
            len(prompt),
            len(images) if images else 0,
        )
        return result

    @retry_with_backoff(max_retries=3, initial_delay=1.0, jitter=True)
    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON conforming to optional schema with retries."""
        if images and not self.supports_vision:
            raise LLMError(f"{self.__class__.__name__} does not support vision/image inputs.")

        start_time = time.perf_counter()
        raw_output = self._raw_generate_json(
            prompt=prompt, schema=schema, system=system, images=images
        )
        elapsed = time.perf_counter() - start_time
        logger.debug(
            "LLM generate_json completed in %.3fs (prompt_len=%d, images=%d)",
            elapsed,
            len(prompt),
            len(images) if images else 0,
        )

        cleaned_json = extract_json_string(raw_output)
        try:
            parsed = json.loads(cleaned_json)
        except json.JSONDecodeError as exc:
            snippet = raw_output[:300] + ("..." if len(raw_output) > 300 else "")
            logger.error(
                "Failed to parse LLM JSON response: %s\nRaw output snippet: %s", exc, snippet
            )
            raise LLMJSONError(
                f"LLM returned invalid JSON: {exc}. Response snippet: {snippet}"
            ) from exc

        if not isinstance(parsed, dict):
            if isinstance(parsed, list):
                return {"items": parsed}
            raise LLMJSONError(f"Expected JSON object (dict), received {type(parsed).__name__}")

        return parsed


# Backward-compatible alias
BaseLLMClient = LLMClient
