import hashlib
import json
from pathlib import Path
import pytest

from app.core.config import settings
from app.services.data_loader import load_normalized_questions, load_raw_questions, load_raw_reports
from app.services.grouping import group_reports_by_question
from app.services.precheck import (
    check_blank_options,
    check_duplicate_options,
    check_existing_error_history,
    check_malformed_answers,
    check_missing_figure_assets,
    check_missing_options,
    check_raw_markup,
    check_suspicious_or_missing_units,
    run_all_prechecks,
)


def test_all_43_questions_processed_once():
    """Verifies that all 43 questions are loaded and processed exactly once in precheck."""
    questions = load_normalized_questions()
    assert len(questions) == 43, f"Expected 43 questions, got {len(questions)}"
    
    unique_ids = set(q.id for q in questions)
    assert len(unique_ids) == 43, "Duplicate question IDs found among processed questions"

    findings = run_all_prechecks(questions)
    assert isinstance(findings, list)
    # Findings must only reference valid question IDs
    for f in findings:
        assert f.question_id in unique_ids


def test_all_44_reports_assigned_to_exactly_one_group():
    """Verifies that all 44 reports are assigned to exactly one group across the 39 groups."""
    raw_reports = load_raw_reports()
    assert len(raw_reports) == 44

    groups = group_reports_by_question()
    assigned_report_ids = []
    for g in groups:
        for r in g.reports:
            assigned_report_ids.append(r.reportId)

    assert len(assigned_report_ids) == 44, f"Expected 44 assigned reports, got {len(assigned_report_ids)}"
    assert len(set(assigned_report_ids)) == 44, "Reports were duplicated across groups"
    
    expected_report_ids = set(r["reportId"] for r in raw_reports)
    assert set(assigned_report_ids) == expected_report_ids


def test_exact_report_id_to_question_id_mapping_reconciliation():
    """Permanent regression test: Every single one of the 44 reports must map to
    its exact, canonical questionId as defined in raw reports.json.
    
    Explicitly checks both live group_reports_by_question() and persisted data/report_groups.json.
    Guarantees no report-to-question transposition or misassignment bug can ever occur.
    """
    raw_reports = load_raw_reports()
    expected_mapping = {r["reportId"]: r["questionId"] for r in raw_reports}
    assert len(expected_mapping) == 44

    # 1. Verify live grouping service output
    live_groups = group_reports_by_question()
    actual_live_mapping = {}
    for g in live_groups:
        for r in g.reports:
            actual_live_mapping[r.reportId] = g.question_id

    assert len(actual_live_mapping) == 44
    assert actual_live_mapping == expected_mapping, "Live grouping reportId-to-questionId mapping mismatch!"

    # 2. Verify persisted artifact data/report_groups.json
    artifact_path = settings.DATA_RAW_DIR.parent / "report_groups.json"
    assert artifact_path.exists(), "data/report_groups.json does not exist"
    with open(artifact_path, "r", encoding="utf-8") as f:
        persisted_groups = json.load(f)

    actual_persisted_mapping = {}
    for g in persisted_groups:
        for r in g["reports"]:
            actual_persisted_mapping[r["reportId"]] = g["question_id"]

    assert len(actual_persisted_mapping) == 44
    assert actual_persisted_mapping == expected_mapping, "Persisted report_groups.json mapping mismatch!"

    # 3. Explicit regression asserts on user-highlighted cases
    assert actual_persisted_mapping["R020"] == "68c8153cfb6b2f16e2d3ceaf"
    assert actual_persisted_mapping["R021"] == "68f21caf941cda588bc04365"
    assert actual_persisted_mapping["R022"] == "61ee6c9d90a1a968a168686b"
    assert actual_persisted_mapping["R043"] == "636283dbe3770c24f866e6d6"
    assert actual_persisted_mapping["R044"] == "68dea577d0cda73d07e9391c"

    # 4. Assert individual equality across all 44 report IDs
    for rid, expected_qid in expected_mapping.items():
        assert actual_persisted_mapping[rid] == expected_qid, (
            f"Mapping discrepancy on report {rid}: expected {expected_qid}, got {actual_persisted_mapping[rid]}"
        )



def test_39_groups_produced():
    """Verifies that grouping produces exactly 39 distinct question groups."""
    groups = group_reports_by_question()
    assert len(groups) == 39, f"Expected 39 groups, got {len(groups)}"

    group_qids = [g.question_id for g in groups]
    assert len(set(group_qids)) == 39, "Duplicate question_id across groups"

    # Also verify the persisted artifact data/report_groups.json
    artifact_path = settings.DATA_RAW_DIR.parent / "report_groups.json"
    if artifact_path.exists():
        with open(artifact_path, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        assert len(persisted) == 39
        persisted_reports_count = sum(g["report_count"] for g in persisted)
        assert persisted_reports_count == 44


def test_multi_report_groupings():
    """Verifies explicit multi-report groupings:
    - R001/R002/R003 grouped together (question 60f744b3f1b9bc7cc7b4a949)
    - R007/R008 grouped together (question 60f742f6660d187cc13a8078)
    - R009/R010 grouped together (question 622f08d7b70e4b50e4500a1b)
    - R018/R019 grouped together (question 612151a6a34397610a9a2e58)
    """
    groups = group_reports_by_question()
    group_map = {g.question_id: [r.reportId for r in g.reports] for g in groups}

    assert group_map["60f744b3f1b9bc7cc7b4a949"] == ["R001", "R002", "R003"]
    assert group_map["60f742f6660d187cc13a8078"] == ["R007", "R008"]
    assert group_map["622f08d7b70e4b50e4500a1b"] == ["R009", "R010"]
    assert group_map["612151a6a34397610a9a2e58"] == ["R018", "R019"]


def test_missing_d_detection():
    """Verifies deterministic detection of missing Option D on question 622f08d7b70e4b50e4500a1b."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "622f08d7b70e4b50e4500a1b")
    
    findings = check_missing_options(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "MISSING_OPTIONS"
    assert f.severity == "high"
    assert "D" in f.evidence
    assert f.source_field == "options"
    assert f.requires_investigation is True


def test_blank_option_detection():
    """Verifies deterministic detection of blank Option C on question 68e872546e45ba37dcc16bc0."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "68e872546e45ba37dcc16bc0")

    findings = check_blank_options(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "BLANK_OPTION"
    assert f.severity == "high"
    assert "Option (C)" in f.evidence
    assert f.source_field == "options.C"
    assert f.requires_investigation is True


def test_missing_figure_detection_for_r025():
    """Verifies deterministic missing figure detection on question 622df25ab70e4b50e44ff837 (report R025)."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "622df25ab70e4b50e44ff837")

    # Confirm report R025 references this question
    assert "R025" in q.report_ids

    findings = check_missing_figure_assets(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "MISSING_FIGURE_ASSET"
    assert f.severity == "critical"
    assert "quesImages is empty" in f.evidence
    assert f.source_field == "quesImages"
    assert f.requires_investigation is True


def test_malformed_answer_detection_both_mcq_anomalies():
    """Verifies detection of both MCQ malformed answer structures:
    - 68f21caf941cda588bc04365: ['', 'B']
    - 68c8153cfb6b2f16e2d3ceaf: ['A, B, D']
    """
    questions = load_normalized_questions()

    # Case 1: empty string in list
    q1 = next(q for q in questions if q.id == "68f21caf941cda588bc04365")
    f1 = check_malformed_answers(q1)
    assert len(f1) == 1
    assert f1[0].check_id == "MALFORMED_ANSWER"
    assert f1[0].severity == "high"
    assert "empty_string_in_answer_list" in f1[0].evidence

    # Case 2: comma-separated string inside list
    q2 = next(q for q in questions if q.id == "68c8153cfb6b2f16e2d3ceaf")
    f2 = check_malformed_answers(q2)
    assert len(f2) == 1
    assert f2[0].check_id == "MALFORMED_ANSWER"
    assert f2[0].severity == "high"
    assert "comma_separated_string_in_list" in f2[0].evidence


def test_error_history_detection_for_r017():
    """Verifies detection of existing error history on question 6208e80a9cb2ab67dac61bd0 (report R017)."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "6208e80a9cb2ab67dac61bd0")

    assert "R017" in q.report_ids
    findings = check_existing_error_history(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "EXISTING_ERROR_HISTORY"
    assert f.severity == "info"
    assert "faculty" in f.evidence
    assert "Spelling mistake" in f.evidence


def test_duplicate_options_detection():
    """Verifies detection of identical options B and C on question 6956d79788d7701e5617bc29."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "6956d79788d7701e5617bc29")

    findings = check_duplicate_options(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "DUPLICATE_OPTIONS"
    assert f.severity == "high"
    assert "(B)" in f.evidence and "(C)" in f.evidence
    assert "0 W" in f.evidence


def test_raw_markup_detection():
    """Verifies detection of leaked raw LaTeX markup on question 63765a28f1d8416ae0408d89."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "63765a28f1d8416ae0408d89")

    findings = check_raw_markup(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "RAW_MARKUP_LEAK"
    assert "\\frac" in f.evidence


def test_suspicious_or_missing_unit_detection():
    """Verifies detection of missing unit specification on integer question 5fc60508028950133eac8963."""
    questions = load_normalized_questions()
    q = next(q for q in questions if q.id == "5fc60508028950133eac8963")

    findings = check_suspicious_or_missing_units(q)
    assert len(findings) == 1
    f = findings[0]
    assert f.check_id == "SUSPICIOUS_OR_MISSING_UNIT"
    assert "frictional force" in f.evidence


def test_no_raw_data_mutation():
    """Verifies that raw question, report, and taxonomy files are NEVER mutated."""
    raw_files = [
        settings.DATA_RAW_DIR / "questions.json",
        settings.DATA_RAW_DIR / "reports.json",
        settings.DATA_RAW_DIR / "taxonomy.json",
    ]

    hashes_before = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in raw_files
    }

    # Execute full normalization, precheck, and grouping pipeline
    qs = load_normalized_questions()
    findings = run_all_prechecks(qs)
    groups = group_reports_by_question()

    hashes_after = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in raw_files
    }

    for p in raw_files:
        assert hashes_before[p] == hashes_after[p], f"Raw file mutated: {p.name}"

