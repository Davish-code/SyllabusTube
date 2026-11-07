"""Google Gemini LLM provider implementation using google-genai SDK."""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import errors, types

from syllabustube.exceptions import QuotaExceededError
from syllabustube.llm.base import LLMClient, LLMError

logger = logging.getLogger("syllabustube.llm.gemini")


class GeminiClient(LLMClient):
    """Client for Google Gemini models via official google-genai SDK."""

    supports_vision: bool = True

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.1,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

        if not self.api_key:
            logger.warning(
                "GeminiClient initialized without API key. Calls will fail unless configured in environment."
            )

    def _get_client(self) -> genai.Client:
        if not self.api_key:
            raise LLMError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env or environment."
            )
        return genai.Client(api_key=self.api_key)

    def _handle_api_error(self, exc: Exception) -> None:
        """Inspect exception and translate quota / rate limit errors into QuotaExceededError."""
        err_msg = str(exc)
        code = getattr(exc, "code", None)
        if (
            code == 429
            or "RESOURCE_EXHAUSTED" in err_msg
            or "429" in err_msg
            or "quota" in err_msg.lower()
        ):
            logger.error("Gemini rate or quota limit reached: %s", err_msg)
            raise QuotaExceededError(
                message=f"Gemini API quota exceeded: {err_msg}", service="gemini"
            ) from exc
        raise LLMError(f"Gemini API error: {err_msg}") from exc

    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=self.temperature,
        )
        contents: list[Any] = []
        if images:
            for img_bytes in images:
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
        contents.append(prompt)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            if response.usage_metadata:
                logger.debug(
                    "Gemini usage: prompt_tokens=%s, candidate_tokens=%s",
                    response.usage_metadata.prompt_token_count,
                    response.usage_metadata.candidates_token_count,
                )
            return response.text or ""
        except errors.APIError as exc:
            self._handle_api_error(exc)
        except Exception as exc:
            if "quota" in str(exc).lower() or "429" in str(exc):
                self._handle_api_error(exc)
            raise LLMError(f"Gemini request failed: {exc}") from exc
        return ""

    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=schema if schema else None,
        )

        contents: list[Any] = []
        if images:
            for img_bytes in images:
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
        contents.append(prompt)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            if response.usage_metadata:
                logger.debug(
                    "Gemini JSON usage: prompt_tokens=%s, candidate_tokens=%s",
                    response.usage_metadata.prompt_token_count,
                    response.usage_metadata.candidates_token_count,
                )
            return response.text or "{}"
        except errors.APIError as exc:
            self._handle_api_error(exc)
        except Exception as exc:
            if "quota" in str(exc).lower() or "429" in str(exc):
                self._handle_api_error(exc)
            raise LLMError(f"Gemini JSON request failed: {exc}") from exc
        return "{}"
