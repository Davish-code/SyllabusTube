"""Unit tests for syllabus structuring, chunk merging, ID generation, and caching."""

import json
from pathlib import Path
from typing import Any

from syllabustube.cache.store import CacheStore
from syllabustube.config import AppConfig
from syllabustube.ingest.pdf_parser import ParsedDocument, ParsedPage
from syllabustube.ingest.syllabus_structurer import (
    post_process_syllabus,
    split_text_at_boundaries,
    structure_syllabus,
)
from syllabustube.llm.base import LLMClient
from syllabustube.models import Module, Syllabus, Topic


class CannedLLMClient(LLMClient):
    supports_vision: bool = True

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.call_idx = 0
        self.call_count = 0
        self.model = "test-canned-model"

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
        if self.call_idx < len(self.responses):
            res = self.responses[self.call_idx]
            self.call_idx += 1
            return json.dumps(res)
        return json.dumps(self.responses[-1])


def test_split_text_at_boundaries() -> None:
    text = (
        "UNIT 1: Fundamentals of Computing\nBits, bytes, logic gates.\n\n"
        "UNIT 2: Operating Systems\nProcesses, threads, memory management.\n\n"
        "UNIT 3: Database Systems\nRelational algebra, SQL, ACID."
    )
    # Split with small max_chunk_chars
    chunks = split_text_at_boundaries(text, max_chunk_chars=80)
    assert len(chunks) == 3
    assert "UNIT 1" in chunks[0]
    assert "UNIT 2" in chunks[1]
    assert "UNIT 3" in chunks[2]


def test_post_process_id_generation_and_dedupe() -> None:
    t1 = Topic(
        id="old_id1", name="Vectors", keywords=["vectors", "ARROWS", "VECTORS"], depth="intro"
    )
    t2 = Topic(id="old_id2", name="vectors", keywords=["linear algebra"])  # Duplicate of t1
    t3 = Topic(id="old_id3", name="Matrices", keywords=["matrices", "TRANSFORMATION"])

    mod = Module(id="mod_raw", number=1, name="Linear Algebra Basics", topics=[t1, t2, t3])
    raw_syllabus = Syllabus(subject="Math 101", modules=[mod])

    cleaned = post_process_syllabus(raw_syllabus, hints={"subject": "Applied Linear Algebra"})
    assert cleaned.subject == "Applied Linear Algebra"
    assert len(cleaned.modules) == 1
    assert cleaned.modules[0].id == "m1"
    assert cleaned.modules[0].number == 1

    # Should deduplicate t1 and t2
    topics = cleaned.modules[0].topics
    assert len(topics) == 2
    assert topics[0].id == "m1.t1"
    assert topics[0].name == "Vectors"
    # Keywords should not include "vectors" (duplicating topic name)
    assert "vectors" not in topics[0].keywords
    assert "arrows" in topics[0].keywords

    assert topics[1].id == "m1.t2"
    assert topics[1].name == "Matrices"


def test_structure_syllabus_caching(tmp_path: Path) -> None:
    db_file = tmp_path / "test_cache.sqlite"
    cache = CacheStore(db_file)

    canned_response = {
        "subject": "Distributed Systems",
        "university": "Stanford",
        "modules": [
            {
                "id": "raw_1",
                "number": 1,
                "name": "Consensus",
                "topics": [
                    {
                        "id": "raw_t1",
                        "name": "Paxos and Raft",
                        "description": "Leader election and log replication.",
                        "keywords": ["consensus", "raft", "paxos"],
                        "depth": "university",
                    }
                ],
            }
        ],
    }

    mock_llm = CannedLLMClient([canned_response])
    cfg = AppConfig()
    cfg.cache.path = str(db_file)

    doc = ParsedDocument(
        pdf_path="test.pdf",
        file_hash="abc123hash",
        page_count=1,
        pages=[ParsedPage(page_number=1, text="Distributed Systems Syllabus", char_count=30)],
        full_text="Distributed Systems Syllabus: Consensus, Paxos and Raft",
    )

    # 1. First call: executes LLM
    syllabus1 = structure_syllabus(doc, mock_llm, config=cfg, cache_store=cache)
    assert mock_llm.call_count == 1
    assert syllabus1.subject == "Distributed Systems"
    assert len(syllabus1.modules) == 1

    # 2. Second call: hits cache, 0 new LLM calls
    syllabus2 = structure_syllabus(doc, mock_llm, config=cfg, cache_store=cache)
    assert mock_llm.call_count == 1  # Still 1!
    assert syllabus2.subject == syllabus1.subject
    assert syllabus2.modules[0].topics[0].id == "m1.t1"

    cache.close()
