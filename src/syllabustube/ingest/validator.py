"""Validation checks and automatic LLM repair for extracted Syllabus models."""

from __future__ import annotations

import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from syllabustube.llm.base import LLMClient
from syllabustube.models import Syllabus

logger = logging.getLogger("syllabustube.ingest.validator")

NOISE_PATTERNS = [
    re.compile(r"\b(?:CO[0-9]|course\s+outcomes?|learning\s+outcomes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:marking\s+scheme|grading\s+scheme|evaluation\s+criteria)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:textbooks?|references?|reference\s+books?|bibliography|isbn\s*[\d-]*)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:credit\s+hours?|lecture\s+hours?|tutorial\s+hours?|prerequisites?)\b", re.IGNORECASE
    ),
    re.compile(r"\b(?:exam\s+pattern|question\s+paper\s+format)\b", re.IGNORECASE),
]


class ValidationIssue(BaseModel):
    """Specific error or warning identified in a parsed syllabus."""

    code: str = Field(description="Unique issue classification code")
    message: str = Field(description="Explanatory message")
    severity: Literal["error", "warning"] = Field(description="Severity tier")
    module_id: str | None = Field(default=None, description="Affected module ID if applicable")
    topic_id: str | None = Field(default=None, description="Affected topic ID if applicable")


class ValidationReport(BaseModel):
    """Aggregate result of syllabus validation checks."""

    is_valid: bool = Field(description="True if no fatal errors exist")
    errors: list[ValidationIssue] = Field(
        default_factory=list, description="Critical structural errors"
    )
    warnings: list[ValidationIssue] = Field(
        default_factory=list, description="Non-fatal warnings and anomalies"
    )

    @property
    def total_issues(self) -> int:
        return len(self.errors) + len(self.warnings)


def validate_syllabus(syllabus: Syllabus, page_count: int = 1) -> ValidationReport:
    """Run comprehensive structural and content quality checks against a parsed Syllabus.

    Checks:
    - At least 1 module
    - No empty modules
    - No empty, excessively short (<3 chars) or excessively long (>200 chars) topic names
    - Duplicate topic names
    - Suspicious topic counts (too few or too many relative to page count)
    - Topics resembling administrative noise (outcomes, textbooks, credit hours)
    - Missing keywords
    - Module numbering gaps
    """
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    # 1. At least 1 module
    if not syllabus.modules:
        errors.append(
            ValidationIssue(
                code="NO_MODULES",
                message="Syllabus does not contain any modules or units.",
                severity="error",
            )
        )
        return ValidationReport(is_valid=False, errors=errors, warnings=warnings)

    all_topics = syllabus.all_topics()

    # 2. Suspicious total topic counts
    if len(all_topics) < 2:
        warnings.append(
            ValidationIssue(
                code="TOO_FEW_TOPICS",
                message=f"Syllabus contains only {len(all_topics)} topic(s), which may indicate incomplete extraction.",
                severity="warning",
            )
        )
    elif len(all_topics) > max(120, page_count * 40):
        warnings.append(
            ValidationIssue(
                code="TOO_MANY_TOPICS",
                message=f"Syllabus contains an unusually high number of topics ({len(all_topics)}).",
                severity="warning",
            )
        )

    # 3. Module checks & numbering gaps
    expected_number = 1
    seen_topic_names: dict[str, str] = {}

    for mod in syllabus.modules:
        if mod.number != expected_number:
            warnings.append(
                ValidationIssue(
                    code="MODULE_NUMBER_GAP",
                    message=f"Module '{mod.id}' has number {mod.number}, but expected sequential number {expected_number}.",
                    severity="warning",
                    module_id=mod.id,
                )
            )
        expected_number += 1

        if not mod.topics:
            errors.append(
                ValidationIssue(
                    code="EMPTY_MODULE",
                    message=f"Module '{mod.id}' ('{mod.name}') contains zero topics.",
                    severity="error",
                    module_id=mod.id,
                )
            )
            continue

        for topic in mod.topics:
            t_name = topic.name.strip()
            # 4. Topic name lengths
            if len(t_name) < 3:
                errors.append(
                    ValidationIssue(
                        code="TOPIC_NAME_TOO_SHORT",
                        message=f"Topic '{topic.id}' has an invalid/too short name: '{t_name}'.",
                        severity="error",
                        module_id=mod.id,
                        topic_id=topic.id,
                    )
                )
            elif len(t_name) > 200:
                warnings.append(
                    ValidationIssue(
                        code="TOPIC_NAME_TOO_LONG",
                        message=f"Topic '{topic.id}' has an unusually long name ({len(t_name)} characters).",
                        severity="warning",
                        module_id=mod.id,
                        topic_id=topic.id,
                    )
                )

            # 5. Duplicate topics
            normalized_name = re.sub(r"[^a-z0-9]", "", t_name.lower())
            if normalized_name in seen_topic_names:
                prior_id = seen_topic_names[normalized_name]
                warnings.append(
                    ValidationIssue(
                        code="DUPLICATE_TOPIC",
                        message=f"Topic '{topic.id}' ('{t_name}') duplicates topic '{prior_id}'.",
                        severity="warning",
                        module_id=mod.id,
                        topic_id=topic.id,
                    )
                )
            else:
                seen_topic_names[normalized_name] = topic.id

            # 6. Noise checks (course outcomes, textbook citations)
            for pattern in NOISE_PATTERNS:
                if pattern.search(t_name) or pattern.search(topic.description):
                    warnings.append(
                        ValidationIssue(
                            code="NOISE_TOPIC",
                            message=f"Topic '{topic.id}' ('{t_name}') appears to describe administrative noise or outcomes.",
                            severity="warning",
                            module_id=mod.id,
                            topic_id=topic.id,
                        )
                    )
                    break

            # 7. Missing keywords
            if not topic.keywords:
                warnings.append(
                    ValidationIssue(
                        code="MISSING_KEYWORDS",
                        message=f"Topic '{topic.id}' ('{t_name}') has no keywords defined.",
                        severity="warning",
                        module_id=mod.id,
                        topic_id=topic.id,
                    )
                )

    is_valid = len(errors) == 0
    return ValidationReport(is_valid=is_valid, errors=errors, warnings=warnings)


def repair_syllabus_with_llm(
    syllabus: Syllabus,
    errors: list[ValidationIssue],
    llm: LLMClient,
) -> Syllabus:
    """Prompt the LLM to repair schema or structural validation errors."""
    logger.info("Attempting automatic LLM repair for %d validation error(s)...", len(errors))

    system_prompt = (
        "You are an academic curriculum validator. You are given a syllabus JSON containing validation errors. "
        "Fix all listed errors: remove noise topics, ensure all modules have valid topics, ensure topic names are concise (3-100 chars), "
        "and return only valid repaired JSON matching the Syllabus schema."
    )

    error_lines = [f"- [{err.code}] {err.message}" for err in errors]
    user_prompt = (
        f"Validation Errors to Fix:\n"
        f"{chr(10).join(error_lines)}\n\n"
        f"Faulty Syllabus JSON:\n"
        f"{syllabus.model_dump_json(indent=2)}\n\n"
        f"Provide the corrected JSON:"
    )

    try:
        repaired_dict = llm.generate_json(prompt=user_prompt, system=system_prompt)
        from syllabustube.ingest.syllabus_structurer import post_process_syllabus

        repaired_syllabus = Syllabus.model_validate(repaired_dict)
        return post_process_syllabus(repaired_syllabus)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM repair attempt failed: %s. Retaining original syllabus.", exc)
        return syllabus


def validate_and_repair(
    syllabus: Syllabus,
    llm: LLMClient | None = None,
    page_count: int = 1,
    max_retries: int = 1,
) -> tuple[Syllabus, ValidationReport]:
    """Validate a syllabus, executing one automatic repair cycle if errors are found.

    Returns:
        Tuple of (possibly_repaired_syllabus, final_validation_report).
    """
    report = validate_syllabus(syllabus, page_count=page_count)
    if report.is_valid or not llm or max_retries <= 0:
        return syllabus, report

    # Trigger automatic repair
    repaired_syllabus = repair_syllabus_with_llm(syllabus, report.errors, llm)
    repaired_report = validate_syllabus(repaired_syllabus, page_count=page_count)

    if repaired_report.is_valid or len(repaired_report.errors) < len(report.errors):
        logger.info("LLM repair succeeded or improved the syllabus structure.")
        return repaired_syllabus, repaired_report

    logger.warning(
        "LLM repair did not resolve all errors; returning best available structure with warnings."
    )
    return repaired_syllabus, repaired_report
