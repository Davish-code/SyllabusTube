"""Unit tests for configuration loading, validation, and secret masking."""

from pathlib import Path

import pytest

from syllabustube.config import (
    AppConfig,
    ConfigurationError,
    load_config,
    mask_secret,
)


def test_mask_secret() -> None:
    assert mask_secret(None) == "[NOT SET]"
    assert mask_secret("") == "[NOT SET]"
    assert mask_secret("short") == "***"
    assert mask_secret("AIzaSy1234567890abcdefghijklmnopqrst") == "AIz...qrst"


def test_default_config_valid() -> None:
    config = AppConfig()
    assert config.llm.provider in ("gemini", "ollama")
    assert config.quota.daily_limit == 10000
    assert config.matching.strictness == 0.7


def test_load_valid_config(tmp_path: Path) -> None:
    yaml_content = """
llm:
  provider: "ollama"
  model: "llama3.1"
  temperature: 0.2
  timeout: 45.0
discovery:
  max_playlists_per_module: 4
matching:
  strictness: 0.85
  tier_thresholds:
    high: 0.9
    review: 0.6
"""
    cfg_file = tmp_path / "custom_config.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    config = load_config(config_path=cfg_file)
    assert config.llm.provider == "ollama"
    assert config.llm.temperature == 0.2
    assert config.discovery.max_playlists_per_module == 4
    assert config.matching.strictness == 0.85
    assert config.matching.tier_thresholds.high == 0.9


def test_invalid_config_raises_error(tmp_path: Path) -> None:
    # strictness must be <= 1.0
    yaml_content = """
matching:
  strictness: 2.5
"""
    cfg_file = tmp_path / "invalid_config.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_path=cfg_file)


def test_nonexistent_config_raises_error(tmp_path: Path) -> None:
    missing_file = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigurationError):
        load_config(config_path=missing_file)
