"""Unit tests for syllabus validation checks and automatic repair."""

import json
from typing import Any

from syllabustube.ingest.validator import validate_and_repair, validate_syllabus
from syllabustube.llm.base import LLMClient
from syllabustube.models import Module, Syllabus, Topic


class RepairMockLLM(LLMClient):
    supports_vision: bool = False

    def __init__(self, repaired_data: dict[str, Any]) -> None:
        self.repaired_data = repaired_data
        self.call_count = 0

    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        return ""

    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        self.call_count += 1
        return json.dumps(self.repaired_data)


def test_valid_syllabus_passes() -> None:
    t1 = Topic(
        id="m1.t1",
        name="Vectors and Matrices",
        description="Intro to linear spaces",
        keywords=["vectors", "matrices"],
    )
    t2 = Topic(
        id="m1.t2",
        name="Linear Transformations",
        description="Mapping vector spaces",
        keywords=["linear mapping"],
    )
    t3 = Topic(
        id="m2.t1",
        name="Eigenvalues",
        description="Characteristic equations",
        keywords=["eigenvalues"],
    )

    m1 = Module(id="m1", number=1, name="Fundamentals", topics=[t1, t2])
    m2 = Module(id="m2", number=2, name="Spectral Theory", topics=[t3])

    syllabus = Syllabus(subject="Linear Algebra", modules=[m1, m2])
    report = validate_syllabus(syllabus, page_count=2)

    assert report.is_valid
    assert len(report.errors) == 0
    assert len(report.warnings) == 0


def test_no_modules_error() -> None:
    syllabus = Syllabus(subject="Empty Course", modules=[])
    report = validate_syllabus(syllabus)
    assert not report.is_valid
    assert any(e.code == "NO_MODULES" for e in report.errors)


def test_empty_module_error() -> None:
    m1 = Module(id="m1", number=1, name="Empty Module", topics=[])
    syllabus = Syllabus(subject="Course", modules=[m1])
    report = validate_syllabus(syllabus)
    assert not report.is_valid
    assert any(e.code == "EMPTY_MODULE" for e in report.errors)


def test_topic_name_too_short_error() -> None:
    t = Topic(id="m1.t1", name="A", keywords=["letter"])
    m1 = Module(id="m1", number=1, name="Module 1", topics=[t])
    syllabus = Syllabus(subject="Course", modules=[m1])
    report = validate_syllabus(syllabus)
    assert not report.is_valid
    assert any(e.code == "TOPIC_NAME_TOO_SHORT" for e in report.errors)


def test_duplicate_topic_warning() -> None:
    t1 = Topic(id="m1.t1", name="Fourier Transform", keywords=["fourier"])
    t2 = Topic(id="m1.t2", name="Fourier Transform", keywords=["signal"])
    m1 = Module(id="m1", number=1, name="Module 1", topics=[t1, t2])
    syllabus = Syllabus(subject="Course", modules=[m1])
    report = validate_syllabus(syllabus)
    assert any(w.code == "DUPLICATE_TOPIC" for w in report.warnings)


def test_noise_topic_warning() -> None:
    t = Topic(id="m1.t1", name="Course Outcomes CO1 and Marking Scheme", keywords=["exam"])
    m1 = Module(id="m1", number=1, name="Module 1", topics=[t])
    syllabus = Syllabus(subject="Course", modules=[m1])
    report = validate_syllabus(syllabus)
    assert any(w.code == "NOISE_TOPIC" for w in report.warnings)


def test_missing_keywords_warning() -> None:
    t1 = Topic(id="m1.t1", name="Normal Topic", keywords=[])
    t2 = Topic(id="m1.t2", name="Another Topic", keywords=["kw"])
    m1 = Module(id="m1", number=1, name="Module 1", topics=[t1, t2])
    syllabus = Syllabus(subject="Course", modules=[m1])
    report = validate_syllabus(syllabus)
    assert any(w.code == "MISSING_KEYWORDS" for w in report.warnings)


def test_module_number_gap_warning() -> None:
    t1 = Topic(id="m1.t1", name="Topic 1", keywords=["k1"])
    t2 = Topic(id="m3.t1", name="Topic 2", keywords=["k2"])
    m1 = Module(id="m1", number=1, name="Mod 1", topics=[t1])
    m3 = Module(id="m3", number=3, name="Mod 3", topics=[t2])
    syllabus = Syllabus(subject="Course", modules=[m1, m3])
    report = validate_syllabus(syllabus)
    assert any(w.code == "MODULE_NUMBER_GAP" for w in report.warnings)


def test_validate_and_repair_flow() -> None:
    # Initially invalid (empty module)
    invalid_mod = Module(id="m1", number=1, name="Invalid Mod", topics=[])
    bad_syllabus = Syllabus(subject="Broken Course", modules=[invalid_mod])

    # Canned repair payload
    fixed_payload = {
        "subject": "Repaired Course",
        "modules": [
            {
                "id": "m1",
                "number": 1,
                "name": "Repaired Mod",
                "topics": [
                    {
                        "id": "m1.t1",
                        "name": "Repaired Topic",
                        "description": "Valid description",
                        "keywords": ["repaired", "topic"],
                        "depth": "university",
                    }
                ],
            }
        ],
    }
    mock_repair_llm = RepairMockLLM(fixed_payload)

    repaired_syllabus, report = validate_and_repair(
        bad_syllabus,
        llm=mock_repair_llm,
        max_retries=1,
    )
    assert mock_repair_llm.call_count == 1
    assert report.is_valid
    assert len(repaired_syllabus.modules[0].topics) == 1
    assert repaired_syllabus.modules[0].topics[0].name == "Repaired Topic"
