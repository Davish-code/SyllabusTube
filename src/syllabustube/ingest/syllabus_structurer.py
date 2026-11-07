"""LLM-based syllabus structuring into Module and Topic domain models with chunking and caching."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from syllabustube.cache.store import CacheStore
from syllabustube.config import AppConfig, get_config
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.ingest.pdf_parser import ParsedDocument
from syllabustube.llm.base import LLMClient
from syllabustube.models import Module, Syllabus, Topic

logger = logging.getLogger("syllabustube.ingest.structurer")

PROMPT_VERSION = "v1.0"


def load_parse_syllabus_prompt() -> tuple[str, str]:
    """Load system instruction and user template for parsing syllabus text."""
    prompt_file = Path(__file__).parent.parent / "llm" / "prompts" / "parse_syllabus.txt"
    if not prompt_file.exists():
        system = "You are a curriculum parser. Convert syllabus text to structured JSON modules and topics."
        user = "Syllabus Text:\n{{syllabus_text}}"
        return system, user

    content = prompt_file.read_text(encoding="utf-8")
    if "[SYSTEM]" in content and "[USER]" in content:
        parts = content.split("[USER]")
        system = parts[0].replace("[SYSTEM]", "").strip()
        user = parts[1].strip()
    else:
        system = "You are a curriculum parser. Convert syllabus text to structured JSON."
        user = content.strip()
    return system, user


def split_text_at_boundaries(text: str, max_chunk_chars: int) -> list[str]:
    """Split text into manageable chunks along Unit/Module boundaries without splitting mid-topic."""
    if len(text) <= max_chunk_chars:
        return [text]

    # Boundary patterns matching Module / Unit headings
    boundary_regex = re.compile(
        r"(?:\n\s*|\n##\s*)(?=(?:UNIT|MODULE|CHAPTER|PART)\s*[-:]?\s*[0-9IVXLCDM]+)",
        re.IGNORECASE,
    )

    parts = [p.strip() for p in boundary_regex.split(text) if p.strip()]
    if not parts or len(parts) == 1:
        # Fall back to double-newline boundary
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []
        curr_len = 0
        for p in paragraphs:
            if curr_len + len(p) > max_chunk_chars and current:
                chunks.append("\n\n".join(current))
                current = [p]
                curr_len = len(p)
            else:
                current.append(p)
                curr_len += len(p)
        if current:
            chunks.append("\n\n".join(current))
        return chunks

    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for part in parts:
        part_len = len(part)
        if current_length + part_len > max_chunk_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [part]
            current_length = part_len
        else:
            current_chunk.append(part)
            current_length += part_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def _normalize_string_for_dedupe(s: str) -> str:
    """Normalize string to lowercase alphanumeric for near-duplicate comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def post_process_syllabus(syllabus: Syllabus, hints: dict[str, Any] | None = None) -> Syllabus:
    """Clean, deduplicate, renumber, and apply hints to parsed Syllabus."""
    hints = hints or {}

    subject = hints.get("subject") or syllabus.subject or "Untitled Course"
    university = hints.get("university") or syllabus.university

    cleaned_modules: list[Module] = []
    mod_counter = 1

    for mod in syllabus.modules:
        mod_name = mod.name.strip() if mod.name else f"Module {mod_counter}"

        seen_topic_keys: set[str] = set()
        cleaned_topics: list[Topic] = []
        topic_counter = 1

        for topic in mod.topics:
            t_name = topic.name.strip()
            if not t_name or len(t_name) < 2:
                continue

            dedupe_key = _normalize_string_for_dedupe(t_name)
            if dedupe_key in seen_topic_keys:
                continue
            seen_topic_keys.add(dedupe_key)

            # Clean keywords
            cleaned_kws: list[str] = []
            for kw in topic.keywords:
                kw_clean = kw.strip()
                if not kw_clean:
                    continue
                # Remove keyword if identical to topic name
                if kw_clean.lower() == t_name.lower():
                    continue
                # Normalize casing
                if kw_clean.isupper() and len(kw_clean) <= 5:
                    cleaned_kws.append(kw_clean)  # Acronym
                else:
                    cleaned_kws.append(kw_clean.lower())

            # Dedupe keywords
            unique_kws = list(dict.fromkeys(cleaned_kws))

            # Stable topic ID
            topic_id = f"m{mod_counter}.t{topic_counter}"
            depth = (
                topic.depth if topic.depth in ("intro", "university", "advanced") else "university"
            )

            cleaned_topics.append(
                Topic(
                    id=topic_id,
                    name=t_name,
                    description=topic.description.strip(),
                    keywords=unique_kws,
                    depth=depth,
                )
            )
            topic_counter += 1

        if cleaned_topics:
            mod_id = f"m{mod_counter}"
            cleaned_modules.append(
                Module(
                    id=mod_id,
                    number=mod_counter,
                    name=mod_name,
                    topics=cleaned_topics,
                )
            )
            mod_counter += 1

    return Syllabus(
        subject=subject.strip(),
        university=university.strip() if university else None,
        modules=cleaned_modules,
    )


def structure_syllabus(
    doc: ParsedDocument,
    llm: LLMClient,
    hints: dict[str, Any] | None = None,
    config: AppConfig | None = None,
    cache_store: CacheStore | None = None,
) -> Syllabus:
    """Structure parsed syllabus text into typed domain models.

    Args:
        doc: ParsedDocument with page texts and SHA-256 hash.
        llm: LLM client implementation.
        hints: User-specified overrides for subject or university.
        config: Application configuration.
        cache_store: CacheStore instance for caching expensive LLM results.

    Returns:
        Structured and validated Syllabus instance.
    """
    cfg = config or get_config()
    cache = cache_store or CacheStore(cfg.cache.path)
    hints = hints or {}

    subject_hint = hints.get("subject", "")
    university_hint = hints.get("university", "")
    subject_filter = hints.get("subject_filter", subject_hint)

    # 1. Check SQLite cache
    model_name = getattr(llm, "model", "default")
    cache_key = f"syllabus_structure:{doc.file_hash}:{PROMPT_VERSION}:{model_name}:{subject_filter}:{university_hint}"
    cached_data = cache.get(cache_key)

    if cached_data and isinstance(cached_data, dict):
        logger.info(
            "Loaded syllabus structure from cache for document hash '%s' (0 LLM calls).",
            doc.file_hash[:8],
        )
        try:
            cached_syllabus = Syllabus.model_validate(cached_data)
            return post_process_syllabus(cached_syllabus, hints=hints)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cached syllabus data invalid: %s. Re-running LLM structuring.", exc)

    logger.info("Structuring syllabus using LLM model '%s'...", model_name)

    system_prompt, user_template = load_parse_syllabus_prompt()
    chunks = split_text_at_boundaries(doc.full_text, cfg.ingest.max_chars_per_llm_call)

    partial_modules: list[Module] = []
    detected_subject = subject_hint or ""
    detected_university = university_hint or ""

    for idx, chunk in enumerate(chunks):
        logger.info(
            "Processing syllabus chunk %d/%d (%d chars)...", idx + 1, len(chunks), len(chunk)
        )
        prompt = (
            user_template.replace("{{subject_hint}}", subject_hint or "None")
            .replace("{{university_hint}}", university_hint or "None")
            .replace("{{syllabus_text}}", chunk)
        )

        try:
            data = llm.generate_json(prompt=prompt, system=system_prompt)
        except Exception as exc:
            logger.error("LLM call failed for chunk %d: %s", idx + 1, exc)
            raise SyllabusTubeError(f"Failed to structure syllabus text with LLM: {exc}") from exc

        # Extract parsed fields
        if not detected_subject and data.get("subject"):
            detected_subject = str(data["subject"])
        if not detected_university and data.get("university"):
            detected_university = str(data["university"])

        raw_mods = data.get("modules", [])
        if isinstance(raw_mods, list):
            for m in raw_mods:
                if isinstance(m, dict):
                    try:
                        partial_modules.append(Module.model_validate(m))
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Skipping malformed module from LLM: %s", exc)

    raw_syllabus = Syllabus(
        subject=detected_subject or "Untitled Course",
        university=detected_university or None,
        modules=partial_modules,
    )

    final_syllabus = post_process_syllabus(raw_syllabus, hints=hints)

    # Persist in cache
    cache.set(cache_key, final_syllabus.model_dump(), ttl=cfg.cache.ttl_days * 86400)
    logger.info(
        "Successfully structured syllabus with %d modules and %d topics.",
        len(final_syllabus.modules),
        len(final_syllabus.all_topics()),
    )

    return final_syllabus
