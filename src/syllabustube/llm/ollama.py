"""Local Ollama LLM provider implementation via HTTP API."""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

from syllabustube.llm.base import LLMClient, LLMError

logger = logging.getLogger("syllabustube.llm.ollama")


class OllamaClient(LLMClient):
    """Client for local open-source models running via Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1",
        temperature: float = 0.1,
        timeout: float = 60.0,
        supports_vision: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.supports_vision = supports_vision

    def _call_api(self, payload: dict[str, Any]) -> str:
        url = f"{self.base_url}/api/generate"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code != 200:
                    raise LLMError(f"Ollama server returned status {resp.status_code}: {resp.text}")
                data = resp.json()
                eval_count = data.get("eval_count")
                prompt_eval_count = data.get("prompt_eval_count")
                if eval_count or prompt_eval_count:
                    logger.debug(
                        "Ollama usage: prompt_eval_count=%s, eval_count=%s",
                        prompt_eval_count,
                        eval_count,
                    )
                return data.get("response", "")
        except httpx.ConnectError as exc:
            msg = f"Cannot connect to Ollama at '{self.base_url}'. Ensure Ollama daemon is running. ({exc})"
            logger.error(msg)
            raise LLMError(msg) from exc
        except httpx.TimeoutException as exc:
            msg = f"Ollama request to '{self.base_url}' timed out after {self.timeout}s: {exc}"
            logger.error(msg)
            raise LLMError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Ollama HTTP error from '{self.base_url}': {exc}"
            logger.error(msg)
            raise LLMError(msg) from exc

    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if system:
            payload["system"] = system
        if images:
            if not self.supports_vision:
                raise LLMError(f"Ollama model '{self.model}' is not configured to support vision.")
            payload["images"] = [base64.b64encode(img).decode("utf-8") for img in images]
        return self._call_api(payload)

    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": self.temperature},
        }
        if system:
            payload["system"] = system
        if images:
            if not self.supports_vision:
                raise LLMError(f"Ollama model '{self.model}' is not configured to support vision.")
            payload["images"] = [base64.b64encode(img).decode("utf-8") for img in images]

        return self._call_api(payload)
