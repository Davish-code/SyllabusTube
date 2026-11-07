"""Configuration loading, Pydantic validation, and environment overlay."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from syllabustube.exceptions import SyllabusTubeError

logger = logging.getLogger("syllabustube.config")


class ConfigurationError(SyllabusTubeError):
    """Raised when configuration file is missing, malformed, or invalid."""


def mask_secret(secret: str | None) -> str:
    """Mask sensitive string like an API key for safe display in logs."""
    if not secret:
        return "[NOT SET]"
    s = secret.strip()
    if len(s) <= 8:
        return "***"
    return f"{s[:3]}...{s[-4:]}"


class LLMConfig(BaseModel):
    provider: Literal["gemini", "ollama"] = "gemini"
    model: str = "gemini-2.5-flash"
    models: dict[str, str] = Field(default_factory=dict)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    timeout: float = Field(default=30.0, gt=0.0)


class DiscoveryConfig(BaseModel):
    source: Literal["youtube_api", "ytdlp"] = "youtube_api"
    max_playlists_per_module: int = Field(default=5, ge=1)
    min_playlist_videos: int = Field(default=3, ge=1)
    language: str = "en"
    max_video_age_years: int = Field(default=5, ge=1)


class EnrichmentConfig(BaseModel):
    transcript_source: Literal["captions_only", "allow_whisper"] = "captions_only"
    chunk_words: int = Field(default=150, ge=20)
    chunk_overlap: int = Field(default=30, ge=0)


class TierThresholds(BaseModel):
    high: float = Field(default=0.8, ge=0.0, le=1.0)
    review: float = Field(default=0.5, ge=0.0, le=1.0)


class MatchingConfig(BaseModel):
    retrieval_top_k: int = Field(default=10, ge=1)
    rerank_top_k: int = Field(default=5, ge=1)
    strictness: float = Field(default=0.7, ge=0.0, le=1.0)
    verify_twice: bool = False
    tier_thresholds: TierThresholds = Field(default_factory=TierThresholds)


class SelectionWeights(BaseModel):
    coverage: float = Field(default=0.5, ge=0.0)
    focus: float = Field(default=0.2, ge=0.0)
    order: float = Field(default=0.15, ge=0.0)
    quality: float = Field(default=0.15, ge=0.0)


class SelectionConfig(BaseModel):
    max_playlists_selected: int = Field(default=3, ge=1)
    weights: SelectionWeights = Field(default_factory=SelectionWeights)


class ExportConfig(BaseModel):
    default_privacy: Literal["unlisted", "public", "private"] = "unlisted"
    one_playlist_per_module: bool = False


class CacheConfig(BaseModel):
    path: str = "cache/syllabustube.db"
    ttl_days: int = Field(default=30, ge=1)


class QuotaConfig(BaseModel):
    daily_limit: int = Field(default=10000, ge=1)
    search_cost: int = Field(default=100, ge=0)
    list_cost: int = Field(default=1, ge=0)
    insert_cost: int = Field(default=50, ge=0)


class AppConfig(BaseModel):
    """Full application configuration tree with environment overlays."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    enrichment: EnrichmentConfig = Field(default_factory=EnrichmentConfig)
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    quota: QuotaConfig = Field(default_factory=QuotaConfig)

    # API Keys overlaid from environment variables
    gemini_api_key: str | None = None
    youtube_api_key: str | None = None
    google_oauth_client_file: str = "client_secret.json"

    def log_summary(self) -> None:
        """Log a sanitized summary of active configuration."""
        logger.info(
            "Configuration active: LLM provider=%s (%s), Discovery=%s, Gemini Key=%s, YouTube Key=%s",
            self.llm.provider,
            self.llm.model,
            self.discovery.source,
            mask_secret(self.gemini_api_key),
            mask_secret(self.youtube_api_key),
        )


_config_singleton: AppConfig | None = None


def load_config(
    config_path: str | Path | None = None, env_path: str | Path | None = None
) -> AppConfig:
    """Load config.yaml, overlay .env variables, and validate via Pydantic.

    Args:
        config_path: Custom path to config.yaml (defaults to ./config.yaml).
        env_path: Custom path to .env file (defaults to .env in cwd).

    Returns:
        Validated AppConfig instance.

    Raises:
        ConfigurationError: If file not found, unparseable, or schema validation fails.
    """
    # Load .env
    load_dotenv(dotenv_path=env_path or ".env", override=False)

    target_path = Path(config_path or "config.yaml")
    raw_data: dict[str, Any] = {}

    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if content and isinstance(content, dict):
                    raw_data = content
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"Failed to parse YAML configuration at '{target_path}': {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                f"Failed to read configuration file at '{target_path}': {exc}"
            ) from exc
    else:
        if config_path is not None:
            raise ConfigurationError(f"Specified config file not found: {target_path}")
        logger.debug("No config.yaml found at '%s'; using default settings.", target_path)

    # Environment variables overlay
    gemini_key = os.getenv("GEMINI_API_KEY")
    youtube_key = os.getenv("YOUTUBE_API_KEY")
    oauth_file = os.getenv("GOOGLE_OAUTH_CLIENT_FILE", "client_secret.json")

    raw_data["gemini_api_key"] = gemini_key
    raw_data["youtube_api_key"] = youtube_key
    raw_data["google_oauth_client_file"] = oauth_file

    try:
        config = AppConfig(**raw_data)
    except ValidationError as exc:
        raise ConfigurationError(f"Configuration validation failed:\n{exc}") from exc

    return config


def get_config(
    config_path: str | Path | None = None,
    env_path: str | Path | None = None,
    reload: bool = False,
) -> AppConfig:
    """Get or initialize singleton AppConfig instance."""
    global _config_singleton
    if _config_singleton is None or reload:
        _config_singleton = load_config(config_path=config_path, env_path=env_path)
    return _config_singleton
