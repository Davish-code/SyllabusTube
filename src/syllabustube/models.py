"""Pydantic v2 domain models for SyllabusTube."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Topic(BaseModel):
    """A granular concept or learning objective from a syllabus."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the topic (e.g. topic_1_1)")
    name: str = Field(description="Short human-readable title of the topic")
    description: str = Field(default="", description="Detailed summary or explanation of the topic")
    keywords: list[str] = Field(default_factory=list, description="Keywords and search phrases")
    depth: Literal["intro", "university", "advanced"] = Field(
        default="university",
        description="Target educational depth/rigor",
    )


class Module(BaseModel):
    """A high-level course unit containing multiple topics."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique module identifier (e.g. mod_1)")
    number: int = Field(description="Sequential module number (1, 2, ...)")
    name: str = Field(description="Name or title of the module")
    topics: list[Topic] = Field(default_factory=list, description="Topics within this module")


class Syllabus(BaseModel):
    """Structured representation of a parsed course syllabus."""

    model_config = ConfigDict(extra="ignore")

    subject: str = Field(description="Course subject or title")
    university: str | None = Field(default=None, description="Offering institution if detected")
    modules: list[Module] = Field(default_factory=list, description="List of modules")

    def all_topics(self) -> list[Topic]:
        """Return a flattened list of all topics across all modules in order."""
        topics: list[Topic] = []
        for mod in self.modules:
            topics.extend(mod.topics)
        return topics


class Video(BaseModel):
    """Metadata representing a YouTube video."""

    model_config = ConfigDict(extra="ignore")

    video_id: str = Field(description="11-character YouTube video ID")
    title: str = Field(description="Video title")
    channel: str = Field(description="Creator or channel name")
    description: str = Field(default="", description="Video description text")
    duration_seconds: int = Field(default=0, ge=0, description="Duration in seconds")
    published_at: str | None = Field(default=None, description="ISO-8601 publish date")
    views: int = Field(default=0, ge=0, description="Total view count")
    likes: int = Field(default=0, ge=0, description="Like count")
    language: str = Field(default="en", description="Primary audio/caption language")
    chapters: list[dict[str, Any]] = Field(
        default_factory=list, description="Timestamped chapter markers"
    )
    transcript_available: bool = Field(
        default=False, description="Whether captions/transcripts are available"
    )


class TranscriptChunk(BaseModel):
    """A timestamped segment of a video transcript."""

    model_config = ConfigDict(extra="ignore")

    video_id: str = Field(description="Parent video ID")
    start_seconds: float = Field(ge=0.0, description="Start timestamp in seconds")
    end_seconds: float = Field(ge=0.0, description="End timestamp in seconds")
    text: str = Field(description="Transcript content")


class Playlist(BaseModel):
    """A YouTube playlist containing ordered videos."""

    model_config = ConfigDict(extra="ignore")

    playlist_id: str = Field(description="YouTube playlist ID")
    title: str = Field(description="Playlist title")
    channel: str = Field(description="Curator/Channel name")
    videos: list[Video] = Field(default_factory=list, description="Ordered videos in the playlist")


class Match(BaseModel):
    """The mapping between a syllabus topic and a matching video segment."""

    model_config = ConfigDict(extra="ignore")

    topic_id: str = Field(description="ID of the matched topic")
    video_id: str = Field(description="ID of the matched video")
    verdict: Literal["yes", "partial", "no"] = Field(description="LLM verification verdict")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score from retrieval & verification"
    )
    tier: Literal["high", "review", "gap"] = Field(description="Match tier classification")
    evidence_quote: str = Field(
        default="", description="Relevant quote from transcript or description"
    )
    start_seconds: float | None = Field(
        default=None, ge=0.0, description="Starting second for the topic"
    )


class PipelineResult(BaseModel):
    """Final artifact emitted by the SyllabusTube pipeline."""

    model_config = ConfigDict(extra="ignore")

    syllabus: Syllabus = Field(description="Parsed syllabus structure")
    selected_playlists: list[Playlist] = Field(
        default_factory=list, description="Optimally selected playlists"
    )
    matches: list[Match] = Field(
        default_factory=list, description="All verified topic-video matches"
    )
    gaps: list[Topic] = Field(
        default_factory=list, description="Topics with no high/review match found"
    )
    stats: dict[str, Any] = Field(
        default_factory=dict, description="Execution metrics, runtimes, quota used"
    )
