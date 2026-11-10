import pytest
from pathlib import Path
from pydantic import ValidationError

from app.core.config import settings
from app.models.result import ProposedEdit, ResultItem
from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import (
    get_report_groups,
    load_normalized_questions,
    load_raw_questions,
    load_raw_reports,
    load_reports,
    load_taxonomy,
)


def test_raw_files_exist():
    """Verifies that all raw files exist under data/raw/."""
    assert settings.QUESTIONS_PATH.exists(), f"Missing {settings.QUESTIONS_PATH}"
    assert settings.REPORTS_PATH.exists(), f"Missing {settings.REPORTS_PATH}"
    assert settings.TAXONOMY_PATH.exists(), f"Missing {settings.TAXONOMY_PATH}"


def test_question_count():
    """Requirement: Exactly 43 questions."""
    raw_questions = load_raw_questions()
    assert len(raw_questions) == 43, f"Expected 43 questions, found {len(raw_questions)}"


def test_report_count():
    """Requirement: Exactly 44 reports."""
    raw_reports = load_raw_reports()
    assert len(raw_reports) == 44, f"Expected 44 reports, found {len(raw_reports)}"


def test_question_ids_unique():
    """Checks that all question MongoDB IDs (_id) are unique 24-character strings."""
    raw_questions = load_raw_questions()
    q_ids = [q["_id"] for q in raw_questions]
    assert len(q_ids) == 43
    assert len(set(q_ids)) == 43, "Question _id must be strictly unique"
    for qid in q_ids:
        assert isinstance(qid, str) and len(qid) == 24, f"Invalid ObjectId format: {qid}"


def test_report_ids_unique():
    """Requirement: Unique report IDs."""
    raw_reports = load_raw_reports()
    report_ids = [r["reportId"] for r in raw_reports]
    assert len(report_ids) == 44
    assert len(set(report_ids)) == 44, f"Duplicate report IDs found: {len(report_ids) - len(set(report_ids))}"


def test_all_report_question_ids_valid():
    """Requirement: Valid question IDs in reports referencing questions dataset."""
    raw_questions = load_raw_questions()
    raw_reports = load_raw_reports()
    valid_qids = set(q["_id"] for q in raw_questions)

    orphaned_reports = []
    for r in raw_reports:
        qid = r.get("questionId")
        if qid not in valid_qids:
            orphaned_reports.append((r.get("reportId"), qid))

    assert len(orphaned_reports) == 0, f"Found reports referencing invalid question IDs: {orphaned_reports}"


def test_taxonomy_programmatic_loading_and_validity():
    """Requirement: Read all taxonomy verdicts and repairs programmatically. Never hardcode."""
    taxonomy = load_taxonomy()
    verdicts = taxonomy.get_verdicts()
    repairs = taxonomy.get_repairs()

    # Verify verdicts are loaded programmatically and non-empty
    assert len(verdicts) == 7, f"Expected 7 verdicts, got {len(verdicts)}"
    expected_verdicts = {
        "defect",
        "no_error",
        "display_issue",
        "app_issue",
        "language_mode",
        "already_fixed",
        "not_actionable",
    }
    assert set(verdicts.keys()) == expected_verdicts

    # Verify repairs are loaded programmatically and non-empty
    assert len(repairs) == 18, f"Expected 18 repairs, got {len(repairs)}"
    expected_repairs = {
        "spelling",
        "noise",
        "exam_reference",
        "markup_leak",
        "answer_form",
        "notation",
        "stem_data",
        "option_repair",
        "solution_fix",
        "solution_missing",
        "answer_key",
        "type_mismatch",
        "identical_options",
        "diagram",
        "wrong_question",
        "unsound",
        "wrong_chapter",
        "syllabus",
    }
    assert set(repairs.keys()) == expected_repairs

    # Verify auto vs manual breakdown
    auto_repairs = [k for k, v in repairs.items() if v.auto]
    manual_repairs = [k for k, v in repairs.items() if not v.auto]
    assert len(auto_repairs) == 12
    assert len(manual_repairs) == 6
    assert set(manual_repairs) == {
        "identical_options",
        "diagram",
        "wrong_question",
        "unsound",
        "wrong_chapter",
        "syllabus",
    }

    # Verify field scopes
    for rep_name in auto_repairs:
        assert len(repairs[rep_name].fields) > 0, f"Auto repair {rep_name} must declare permitted fields"
    for rep_name in manual_repairs:
        assert len(repairs[rep_name].fields) == 0, f"Manual repair {rep_name} must declare empty fields []"


def test_normalized_schema_preserves_html_and_mathml():
    """Requirement: Produce normalized question schema without discarding original HTML/MathML."""
    raw_questions = load_raw_questions()
    normalized_questions = load_normalized_questions()

    assert len(normalized_questions) == 43

    raw_map = {q["_id"]: q for q in raw_questions}
    mathml_count = 0

    for norm_q in normalized_questions:
        raw_q = raw_map[norm_q.id]
        qtype = raw_q["questionType"]
        raw_payload = raw_q[qtype]

        # Raw HTML must be bit-for-bit identical to original payload
        assert norm_q.raw_question_html == raw_payload["question"], (
            f"Question HTML was modified for {norm_q.id}"
        )
        assert norm_q.raw_solution_html == raw_payload["solution"], (
            f"Solution HTML was modified for {norm_q.id}"
        )

        if "<math" in norm_q.raw_question_html or "<math" in norm_q.raw_solution_html:
            assert norm_q.has_mathml is True
            mathml_count += 1

    # 32 out of 43 questions feature MathML equations in question or solution
    assert mathml_count == 32, f"Expected 32 questions containing MathML, got {mathml_count}"


def test_question_types_distribution():
    """Verifies distribution of scq, integerQuestion, and mcq."""
    normalized_questions = load_normalized_questions()
    types_count = {}
    for q in normalized_questions:
        types_count[q.question_type] = types_count.get(q.question_type, 0) + 1

    assert types_count == {"scq": 31, "integerQuestion": 10, "mcq": 2}


def test_missing_option_question_detection():
    """Verifies Question 622f08d7b70e4b50e4500a1b correctly reflects only 3 options (A, B, C)."""
    normalized_questions = load_normalized_questions()
    target_q = next(q for q in normalized_questions if q.id == "622f08d7b70e4b50e4500a1b")
    opt_keys = [o.key for o in target_q.options]
    assert opt_keys == ["A", "B", "C"], f"Expected ['A', 'B', 'C'], got {opt_keys}"


def test_error_history_preservation():
    """Verifies that the single question with faculty errorHistory is accurately preserved."""
    normalized_questions = load_normalized_questions()
    q_with_history = [q for q in normalized_questions if q.error_history]
    assert len(q_with_history) == 1
    target = q_with_history[0]
    assert target.id == "6208e80a9cb2ab67dac61bd0"
    assert len(target.error_history) == 1
    assert target.error_history[0].actor == "faculty"
    assert "'mere' -> 'more'" in target.error_history[0].note


def test_report_groupings():
    """Verifies report grouping dynamics: 39 reported questions, 4 unreported questions."""
    groups = get_report_groups()
    assert len(groups) == 39, f"Expected 39 unique reported questions, got {len(groups)}"

    normalized_questions = load_normalized_questions()
    unreported = [q for q in normalized_questions if len(q.report_ids) == 0]
    assert len(unreported) == 4, f"Expected 4 unreported questions, got {len(unreported)}"

    # Check the question with 3 reports
    q_three_reports = groups.get("60f744b3f1b9bc7cc7b4a949")
    assert q_three_reports is not None
    assert q_three_reports.report_count == 3
    assert set(r.reportId for r in q_three_reports.reports) == {"R001", "R002", "R003"}


def test_result_contract_validation():
    """Tests Pydantic validation of ResultItem against programmatic taxonomy."""
    # Valid result item
    valid_item = ResultItem(
        reportId="R001",
        questionId="60f744b3f1b9bc7cc7b4a949",
        verdict="defect",
        repair="answer_key",
        edit=ProposedEdit(field="answer", find="C", replace="A"),
        route="auto_apply",
        confidence=0.95,
        evidence="Calculated value 50V matches Option A, whereas key was set to C.",
        student_reply="You're right. The answer key was wrong; it is 50V (Option A). Thank you for reporting!",
    )
    assert valid_item.verdict == "defect"
    assert valid_item.validate_repair_field_scope() is True

    # Invalid verdict should fail Pydantic validation
    with pytest.raises(ValidationError):
        ResultItem(
            reportId="R001",
            questionId="60f744b3f1b9bc7cc7b4a949",
            verdict="non_existent_verdict",
            route="no_change",
            confidence=0.5,
            evidence="test",
            student_reply="test",
        )

    # Invalid repair should fail Pydantic validation
    with pytest.raises(ValidationError):
        ResultItem(
            reportId="R001",
            questionId="60f744b3f1b9bc7cc7b4a949",
            verdict="defect",
            repair="invalid_repair_type",
            route="auto_apply",
            confidence=0.5,
            evidence="test",
            student_reply="test",
        )
