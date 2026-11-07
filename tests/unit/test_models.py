"""Unit tests for Pydantic domain models round-trips and behaviors."""

from syllabustube.models import (
    Match,
    Module,
    PipelineResult,
    Playlist,
    Syllabus,
    Topic,
    Video,
)


def test_topic_model_round_trip() -> None:
    topic = Topic(
        id="t1",
        name="Eigenvalues",
        description="Roots of characteristic polynomial",
        keywords=["eigenvector", "linear algebra"],
        depth="university",
    )
    raw_json = topic.model_dump_json()
    loaded = Topic.model_validate_json(raw_json)
    assert loaded == topic
    assert loaded.depth == "university"


def test_syllabus_all_topics() -> None:
    t1 = Topic(id="t1", name="Topic 1")
    t2 = Topic(id="t2", name="Topic 2")
    t3 = Topic(id="t3", name="Topic 3")

    m1 = Module(id="m1", number=1, name="Module 1", topics=[t1, t2])
    m2 = Module(id="m2", number=2, name="Module 2", topics=[t3])

    syllabus = Syllabus(subject="Linear Algebra", university="MIT", modules=[m1, m2])

    topics = syllabus.all_topics()
    assert len(topics) == 3
    assert [t.id for t in topics] == ["t1", "t2", "t3"]

    # Verify JSON round-trip
    dumped = syllabus.model_dump_json()
    reloaded = Syllabus.model_validate_json(dumped)
    assert reloaded == syllabus


def test_video_and_playlist_round_trip() -> None:
    video = Video(
        video_id="fNk_zzaMoSs",
        title="Vectors | Chapter 1",
        channel="3Blue1Brown",
        duration_seconds=590,
        views=4500000,
        likes=120000,
        transcript_available=True,
    )
    playlist = Playlist(
        playlist_id="PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
        title="Essence of Linear Algebra",
        channel="3Blue1Brown",
        videos=[video],
    )

    dumped = playlist.model_dump_json()
    reloaded = Playlist.model_validate_json(dumped)
    assert reloaded.playlist_id == playlist.playlist_id
    assert len(reloaded.videos) == 1
    assert reloaded.videos[0].video_id == "fNk_zzaMoSs"


def test_match_and_pipeline_result_round_trip() -> None:
    t1 = Topic(id="t1", name="Topic 1")
    m1 = Module(id="m1", number=1, name="Module 1", topics=[t1])
    syllabus = Syllabus(subject="Test Course", modules=[m1])

    match = Match(
        topic_id="t1",
        video_id="fNk_zzaMoSs",
        verdict="yes",
        confidence=0.92,
        tier="high",
        evidence_quote="A vector can be thought of as an arrow.",
        start_seconds=12.5,
    )

    result = PipelineResult(
        syllabus=syllabus,
        selected_playlists=[],
        matches=[match],
        gaps=[],
        stats={"duration_seconds": 4.2},
    )

    data_json = result.model_dump_json()
    reloaded = PipelineResult.model_validate_json(data_json)
    assert reloaded.matches[0].tier == "high"
    assert reloaded.matches[0].confidence == 0.92
