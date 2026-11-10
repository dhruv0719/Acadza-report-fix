import re
from typing import Any, Dict, List, Optional

from app.models.precheck import PrecheckFinding
from app.models.question import NormalizedQuestion


FIGURE_REFERENCE_PATTERN = re.compile(
    r'\b(fig|figure|diagram|shown in figure|as shown|graph)\b',
    re.IGNORECASE,
)

RAW_LATEX_PATTERN = re.compile(
    r'\\[a-zA-Z]{2,}',
)

EXAM_TAG_PATTERN = re.compile(
    r'\((?:NEET|JEE|AIEEE|CBSE|AIPMT)\s*(?:Main|Advanced)?\s*\d{4}\)',
    re.IGNORECASE,
)

DIMENSIONAL_QUANTITIES = [
    "frictional force",
    "friction force",
    "force",
    "velocity",
    "speed",
    "acceleration",
    "wavelength",
    "frequency",
    "energy",
    "power",
    "work",
    "mass",
    "pressure",
    "temperature",
    "current",
    "resistance",
    "capacitance",
    "inductance",
    "magnetic field",
    "electric field",
]

TARGET_UNIT_PATTERN = re.compile(
    r'(\(in\s+[^)]+\)|\[in\s+[^\]]+\]|\bin\s+(?:dioptres|diopters|seconds|sec|cm|mm|m|volts?|joules?|newtons?|watts?|radians?|degrees?|hz)\b|_\s*_\s*_\s*_\s*[a-zA-Z]+)',
    re.IGNORECASE,
)

DIMENSIONLESS_PATTERN = re.compile(
    r'\b(ratio|value of|how many|fraction|factor)\b',
    re.IGNORECASE,
)


def check_missing_options(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for missing options in option-based questions (SCQ / MCQ)."""
    findings = []
    if q.question_type in ("scq", "mcq"):
        expected_keys = {"A", "B", "C", "D"}
        actual_keys = {o.key for o in q.options}
        if len(q.options) < 4 or actual_keys != expected_keys:
            missing = sorted(list(expected_keys - actual_keys))
            findings.append(
                PrecheckFinding(
                    question_id=q.id,
                    check_id="MISSING_OPTIONS",
                    severity="high",
                    evidence=f"Question type '{q.question_type}' has {len(q.options)} options ({sorted(list(actual_keys))}). Missing option(s): {', '.join(missing) if missing else 'insufficient option count'}",
                    source_field="options",
                    requires_investigation=True,
                    details={"missing_keys": missing, "actual_keys": sorted(list(actual_keys))},
                )
            )
    return findings


def check_blank_options(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for blank or whitespace-only options in SCQ / MCQ."""
    findings = []
    if q.question_type in ("scq", "mcq"):
        for opt in q.options:
            if opt.is_blank or not opt.text.strip():
                findings.append(
                    PrecheckFinding(
                        question_id=q.id,
                        check_id="BLANK_OPTION",
                        severity="high",
                        evidence=f"Option ({opt.key}) has blank/empty content (HTML: {repr(opt.html[:80])})",
                        source_field=f"options.{opt.key}",
                        requires_investigation=True,
                        details={"blank_key": opt.key, "raw_html": opt.html},
                    )
                )
    return findings


def check_duplicate_options(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for duplicate or identical options within the same question."""
    findings = []
    if q.question_type in ("scq", "mcq"):
        non_blank = [o for o in q.options if not o.is_blank and o.text.strip()]
        for i in range(len(non_blank)):
            for j in range(i + 1, len(non_blank)):
                opt1, opt2 = non_blank[i], non_blank[j]
                t1 = re.sub(r'\s+', ' ', opt1.text).strip().lower()
                t2 = re.sub(r'\s+', ' ', opt2.text).strip().lower()
                if t1 and t1 == t2:
                    findings.append(
                        PrecheckFinding(
                            question_id=q.id,
                            check_id="DUPLICATE_OPTIONS",
                            severity="high",
                            evidence=f"Options ({opt1.key}) and ({opt2.key}) have identical content: {repr(opt1.text)}",
                            source_field="options",
                            requires_investigation=True,
                            details={"keys": [opt1.key, opt2.key], "identical_text": opt1.text},
                        )
                    )
    return findings


def check_malformed_answers(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for malformed or non-standard answer representations."""
    findings = []
    # If the normalizer already caught answer anomalies:
    for anomaly in q.answer_anomalies:
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="MALFORMED_ANSWER",
                severity="high",
                evidence=f"Malformed answer structure detected: '{anomaly}'. Raw answer value: {repr(q.raw_answer)}",
                source_field="answer",
                requires_investigation=True,
                details={"anomaly": anomaly, "raw_answer": q.raw_answer, "normalized_answer": q.normalized_answer},
            )
        )

    # Additional validations if not already flagged:
    if not q.answer_anomalies:
        if q.question_type == "scq":
            ans_str = str(q.raw_answer).strip().upper()
            if ans_str not in ("A", "B", "C", "D"):
                findings.append(
                    PrecheckFinding(
                        question_id=q.id,
                        check_id="MALFORMED_ANSWER",
                        severity="high",
                        evidence=f"SCQ answer is '{q.raw_answer}', expected single key 'A', 'B', 'C', or 'D'",
                        source_field="answer",
                        requires_investigation=True,
                        details={"raw_answer": q.raw_answer},
                    )
                )
        elif q.question_type == "mcq":
            if not isinstance(q.raw_answer, list) or not q.raw_answer:
                findings.append(
                    PrecheckFinding(
                        question_id=q.id,
                        check_id="MALFORMED_ANSWER",
                        severity="high",
                        evidence=f"MCQ answer must be a non-empty list of option keys, got: {repr(q.raw_answer)}",
                        source_field="answer",
                        requires_investigation=True,
                        details={"raw_answer": q.raw_answer},
                    )
                )
        elif q.question_type == "integerQuestion":
            ans_str = str(q.raw_answer).strip()
            if not ans_str or not ans_str.lstrip("-").isdigit():
                findings.append(
                    PrecheckFinding(
                        question_id=q.id,
                        check_id="MALFORMED_ANSWER",
                        severity="high",
                        evidence=f"Integer question answer is non-integer: {repr(q.raw_answer)}",
                        source_field="answer",
                        requires_investigation=True,
                        details={"raw_answer": q.raw_answer},
                    )
                )
    return findings


def check_missing_content(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for empty or missing question stem or solution content."""
    findings = []
    if not q.stem_text.strip() or not q.raw_question_html.strip():
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="MISSING_QUESTION_CONTENT",
                severity="critical",
                evidence="Question stem is empty or contains no readable text",
                source_field="question",
                requires_investigation=True,
            )
        )
    if not q.solution_text.strip() or not q.raw_solution_html.strip():
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="MISSING_SOLUTION_CONTENT",
                severity="high",
                evidence="Question solution is empty or contains no readable text",
                source_field="solution",
                requires_investigation=True,
            )
        )
    return findings


def check_raw_markup(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for leaked raw LaTeX markup or unrendered commands in HTML outside MathML."""
    findings = []
    for field_name, html_content in [
        ("question", q.raw_question_html),
        ("solution", q.raw_solution_html),
    ]:
        if not html_content:
            continue
        # Strip MathML tags to inspect only non-MathML markup
        html_without_mathml = re.sub(r'<math[\s\S]*?</math>', '', html_content, flags=re.IGNORECASE)
        # Search for raw LaTeX commands like \frac, \sqrt, etc.
        raw_matches = RAW_LATEX_PATTERN.findall(html_without_mathml)
        filtered = [m for m in raw_matches if m not in ('\\n', '\\r', '\\t')]
        if filtered:
            unique_cmds = sorted(list(set(filtered)))
            findings.append(
                PrecheckFinding(
                    question_id=q.id,
                    check_id="RAW_MARKUP_LEAK",
                    severity="medium",
                    evidence=f"Raw LaTeX markup command(s) {unique_cmds} leaked in {field_name} HTML outside MathML tags",
                    source_field=field_name,
                    requires_investigation=True,
                    details={"field": field_name, "commands": unique_cmds},
                )
            )
    return findings


def check_missing_figure_assets(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks if question text references a figure/diagram but no image asset exists."""
    findings = []
    # Check if question stem references a figure
    match = FIGURE_REFERENCE_PATTERN.search(q.stem_text)
    if match:
        has_ques_images = bool(q.ques_images)
        has_img_tag = "<img" in q.raw_question_html.lower()
        if not has_ques_images and not has_img_tag:
            findings.append(
                PrecheckFinding(
                    question_id=q.id,
                    check_id="MISSING_FIGURE_ASSET",
                    severity="critical",
                    evidence=f"Question stem references figure/diagram ('{match.group(0)}'), but quesImages is empty and no <img> tag exists in question HTML",
                    source_field="quesImages",
                    requires_investigation=True,
                    details={"matched_phrase": match.group(0), "ques_images": q.ques_images},
                )
            )
    return findings


def check_existing_error_history(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for prior error history / revision logs on the question."""
    findings = []
    if q.error_history:
        latest = q.error_history[-1]
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="EXISTING_ERROR_HISTORY",
                severity="info",
                evidence=f"Question has {len(q.error_history)} prior revision(s). Latest by {latest.actor} at {latest.at} ({latest.type}): {repr(latest.note)}",
                source_field="errorHistory",
                requires_investigation=True,
                details={
                    "revisions_count": len(q.error_history),
                    "latest_actor": latest.actor,
                    "latest_timestamp": latest.at,
                    "latest_type": latest.type,
                    "latest_note": latest.note,
                },
            )
        )
    return findings


def check_suspicious_or_missing_units(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks integer questions for missing target unit specifications when asking for dimensional quantities."""
    findings = []
    if q.question_type == "integerQuestion":
        stem = q.stem_text
        has_target_unit = bool(TARGET_UNIT_PATTERN.search(stem))
        has_dimensionless = bool(DIMENSIONLESS_PATTERN.search(stem))

        if not (has_target_unit or has_dimensionless):
            stem_lower = stem.lower()
            matched_qty = None
            for qty in DIMENSIONAL_QUANTITIES:
                if qty in stem_lower:
                    matched_qty = qty
                    break

            evidence_detail = f"asks for dimensional quantity '{matched_qty}'" if matched_qty else "asks for numerical answer"
            findings.append(
                PrecheckFinding(
                    question_id=q.id,
                    check_id="SUSPICIOUS_OR_MISSING_UNIT",
                    severity="medium",
                    evidence=f"Integer question {evidence_detail} without specifying the target unit (e.g. '(in N)') or requesting a dimensionless ratio",
                    source_field="stem_text",
                    requires_investigation=True,
                    details={"dimensional_quantity": matched_qty, "stem_ending": stem[-80:]},
                )
            )
    return findings


def check_invalid_metadata(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Checks for invalid or leaked metadata in question records."""
    findings = []
    # Check MongoDB ObjectId validity
    if not re.match(r'^[0-9a-fA-F]{24}$', q.id):
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="INVALID_METADATA",
                severity="critical",
                evidence=f"Question ID '{q.id}' is not a valid 24-character hexadecimal ObjectId",
                source_field="_id",
                requires_investigation=True,
            )
        )

    # Check subject and chapter presence
    if not q.subject or not q.subject.strip():
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="INVALID_METADATA",
                severity="high",
                evidence="Question subject is missing or empty",
                source_field="subject",
                requires_investigation=True,
            )
        )

    if not q.chapter or not q.chapter.strip():
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="INVALID_METADATA",
                severity="high",
                evidence="Question chapter is missing or empty",
                source_field="chapter",
                requires_investigation=True,
            )
        )

    # Check question type validity
    if q.question_type not in ("scq", "mcq", "integerQuestion"):
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="INVALID_METADATA",
                severity="critical",
                evidence=f"Unrecognized questionType '{q.question_type}'",
                source_field="questionType",
                requires_investigation=True,
            )
        )

    # Check for leaked exam tags in question stem
    exam_match = EXAM_TAG_PATTERN.search(q.stem_text)
    if exam_match:
        findings.append(
            PrecheckFinding(
                question_id=q.id,
                check_id="INVALID_METADATA",
                severity="low",
                evidence=f"Exam attribution tag '{exam_match.group(0)}' leaked into question stem instead of structured metadata",
                source_field="stem_text",
                requires_investigation=True,
                details={"leaked_tag": exam_match.group(0)},
            )
        )

    return findings


def run_all_prechecks_for_question(q: NormalizedQuestion) -> List[PrecheckFinding]:
    """Runs all 10 deterministic prechecks on a single normalized question."""
    all_findings = []
    all_findings.extend(check_missing_options(q))
    all_findings.extend(check_blank_options(q))
    all_findings.extend(check_duplicate_options(q))
    all_findings.extend(check_malformed_answers(q))
    all_findings.extend(check_missing_content(q))
    all_findings.extend(check_raw_markup(q))
    all_findings.extend(check_missing_figure_assets(q))
    all_findings.extend(check_existing_error_history(q))
    all_findings.extend(check_suspicious_or_missing_units(q))
    all_findings.extend(check_invalid_metadata(q))
    return all_findings


def run_all_prechecks(questions: List[NormalizedQuestion]) -> List[PrecheckFinding]:
    """Runs all 10 deterministic prechecks across all normalized questions."""
    findings = []
    for q in questions:
        findings.extend(run_all_prechecks_for_question(q))
    return findings
