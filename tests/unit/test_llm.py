"""Unit tests for LLMClient abstractions, fence stripping, and error handling."""

from typing import Any

import pytest

from syllabustube.exceptions import QuotaExceededError
from syllabustube.llm.base import (
    LLMClient,
    LLMError,
    LLMJSONError,
    extract_json_string,
)


class DummyLLMClient(LLMClient):
    """Test stub for LLMClient."""

    def __init__(
        self,
        raw_text: str = "",
        raw_json_str: str = "{}",
        supports_vision: bool = False,
        model: str = "dummy-model",
    ) -> None:
        self.raw_text = raw_text
        self.raw_json_str = raw_json_str
        self.supports_vision = supports_vision
        self.model = model
        self.calls = 0

    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        self.calls += 1
        return self.raw_text

    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        self.calls += 1
        return self.raw_json_str


def test_extract_json_string_fences() -> None:
    fenced = """```json
{
  "subject": "Linear Algebra",
  "modules": []
}
```"""
    cleaned = extract_json_string(fenced)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")
    assert '"subject": "Linear Algebra"' in cleaned


def test_extract_json_string_with_conversational_wrapper() -> None:
    wrapped = 'Here is the parsed syllabus output:\n```json\n{"key": "val"}\n```\nHope this helps!'
    cleaned = extract_json_string(wrapped)
    assert cleaned == '{"key": "val"}'


def test_generate_json_invalid_raises_llm_json_error() -> None:
    client = DummyLLMClient(raw_json_str="This is not JSON at all.")
    with pytest.raises(LLMJSONError) as exc_info:
        client.generate_json("Prompt")
    assert "LLM returned invalid JSON" in str(exc_info.value)


def test_vision_not_supported_raises_error() -> None:
    client = DummyLLMClient(supports_vision=False)
    with pytest.raises(LLMError) as exc_info:
        client.generate_json("Prompt", images=[b"fake_image_bytes"])
    assert "does not support vision" in str(exc_info.value)


def test_quota_exceeded_never_retried() -> None:
    attempts = 0

    class FailingQuotaClient(LLMClient):
        def _raw_generate_text(
            self, prompt: str, system: str | None = None, images: list[bytes] | None = None
        ) -> str:
            nonlocal attempts
            attempts += 1
            raise QuotaExceededError("Rate limit reached", service="gemini")

        def _raw_generate_json(
            self,
            prompt: str,
            schema: dict[str, Any] | None = None,
            system: str | None = None,
            images: list[bytes] | None = None,
        ) -> str:
            return "{}"

    client = FailingQuotaClient()
    with pytest.raises(QuotaExceededError):
        client.generate_text("test")

    # Must abort on 1st attempt, zero retries
    assert attempts == 1
