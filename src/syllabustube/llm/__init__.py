"""LLM module exposing client interfaces, implementations, and factory."""

from __future__ import annotations

from syllabustube.config import AppConfig, get_config
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.llm.base import BaseLLMClient, LLMClient, LLMError, LLMJSONError
from syllabustube.llm.gemini import GeminiClient
from syllabustube.llm.ollama import OllamaClient


def get_llm_client(config: AppConfig | None = None) -> LLMClient:
    """Factory function to instantiate the configured LLM client.

    Args:
        config: Application configuration. If None, loads singleton config.

    Returns:
        Instance of LLMClient (GeminiClient or OllamaClient).
    """
    cfg = config or get_config()
    provider = cfg.llm.provider.lower()

    if provider == "gemini":
        model_name = cfg.llm.models.get("gemini", cfg.llm.model)
        return GeminiClient(
            api_key=cfg.gemini_api_key,
            model=model_name,
            temperature=cfg.llm.temperature,
            timeout=cfg.llm.timeout,
        )
    elif provider == "ollama":
        model_name = cfg.llm.models.get("ollama", cfg.llm.model)
        return OllamaClient(
            base_url=cfg.llm.ollama_base_url,
            model=model_name,
            temperature=cfg.llm.temperature,
            timeout=cfg.llm.timeout,
            supports_vision=cfg.llm.ollama_supports_vision,
        )
    else:
        raise SyllabusTubeError(
            f"Unsupported LLM provider: '{provider}'. Must be 'gemini' or 'ollama'."
        )


__all__ = [
    "BaseLLMClient",
    "GeminiClient",
    "LLMClient",
    "LLMError",
    "LLMJSONError",
    "OllamaClient",
    "get_llm_client",
]
