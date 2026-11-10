import json
from pathlib import Path
import pytest

from app.core.config import settings
from app.models.investigation import (
    BlindSolveOutput,
    InternalReportAssessment,
    ProposedEdit,
    QuestionVerificationOutput,
    SubmissionResultItem,
)
from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import load_normalized_questions, load_raw_reports
from app.services.grouping import group_reports_by_question
from app.services.investigator import (
    investigate_all_groups,
    investigate_question_group,
)
from app.services.llm_adapter import LLMAdapter
from app.services.router import calculate_final_route
from app.services.verifier import HighStakesVerifier


@pytest.fixture
def registry():
    return TaxonomyRegistry.get_default()


@pytest.fixture
def adapter():
    return LLMAdapter()


def test_results_json_schema_and_integrity(registry):
    """Verifies results.json matches the exact 9-field assignment contract with 44 unique reports."""
    results_path = settings.RESULTS_PATH
    assert results_path.exists(), f"results.json not found at {results_path}"

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    assert len(results) == 44, f"Expected 44 reports in results.json, found {len(results)}"
    
    report_ids = [r["reportId"] for r in results]
    assert len(set(report_ids)) == 44, "Duplicate report IDs in results.json"

    raw_reports = load_raw_reports()
    expected_map = {r["reportId"]: r["questionId"] for r in raw_reports}

    allowed_keys = {
        "reportId", "questionId", "verdict", "repair", "edit",
        "route", "confidence", "evidence", "student_reply"
    }

    for item in results:
        # Exact 9 fields, no extra internal keys
        assert set(item.keys()) == allowed_keys, f"Field mismatch in {item['reportId']}: {set(item.keys())}"
        
        # Canonical question mapping
        assert item["questionId"] == expected_map[item["reportId"]]

        # Taxonomy compliance
        assert registry.is_valid_verdict(item["verdict"])
        if item["verdict"] == "defect":
            assert item["repair"] is not None
            assert registry.is_valid_repair(item["repair"])
        else:
            assert item["repair"] is None
            assert item["edit"] is None
            assert item["route"] == "no_change"

        assert 0.0 <= item["confidence"] <= 1.0
        assert len(item["evidence"].strip()) > 0
        assert len(item["student_reply"].strip()) > 0


def test_r004_key_defect_student_suggestion_not_copied(adapter, registry):
    """R004: True answer key defect. Stored key is 'A' (4556), student suggests 8225 (Option B).
    Real answer is 4800 (Option D). Engine must output 'D' and NOT copy 8225.
    """
    groups = group_reports_by_question()
    q_group = next(g for g in groups if any(r.reportId == "R004" for g in groups for r in g.reports if r.reportId == "R004"))
    
    # Locate group containing R004
    target_group = next(g for g in groups if "R004" in [r.reportId for r in g.reports])
    resp = investigate_question_group(target_group, adapter, registry)
    
    ass = next(a for a in resp.report_assessments if a.reportId == "R004")
    assert ass.verdict == "defect"
    assert ass.repair == "answer_key"
    assert ass.edit is not None
    assert ass.edit.field == "answer"
    assert ass.edit.replace == "D"
    assert "8225" not in str(ass.edit.replace)
    assert ass.final_route == "auto_apply"
    assert ass.verification_status == "passed"


def test_r027_prompt_injection_defense(adapter, registry):
    """R027: Adversarial injection attack. Engine must flag injection and NOT obey command."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "R027" in [r.reportId for r in g.reports])
    resp = investigate_question_group(target_group, adapter, registry)

    ass = next(a for a in resp.report_assessments if a.reportId == "R027")
    assert ass.is_prompt_injection is True
    assert ass.verdict == "no_error"
    assert ass.repair is None
    assert ass.edit is None
    assert ass.final_route == "no_change"


def test_r017_correction_history_evaluated(adapter, registry):
    """R017: Evaluated against correction history timestamp. Should be already_fixed."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "R017" in [r.reportId for r in g.reports])
    resp = investigate_question_group(target_group, adapter, registry)

    ass = next(a for a in resp.report_assessments if a.reportId == "R017")
    assert ass.verdict == "already_fixed"
    assert ass.final_route == "no_change"
    assert ass.edit is None


def test_r020_and_r021_answer_formats(adapter, registry):
    """R020 & R021: MCQ formatting anomalies properly normalized and repaired."""
    groups = group_reports_by_question()
    
    # R020
    g20 = next(g for g in groups if "R020" in [r.reportId for r in g.reports])
    r20 = investigate_question_group(g20, adapter, registry)
    ass20 = next(a for a in r20.report_assessments if a.reportId == "R020")
    assert ass20.verdict == "defect"
    assert ass20.repair == "answer_key"
    assert ass20.edit.field == "answer"
    assert ass20.edit.replace == ["A", "B", "D"]
    assert ass20.final_route == "auto_apply"

    # R021
    g21 = next(g for g in groups if "R021" in [r.reportId for r in g.reports])
    r21 = investigate_question_group(g21, adapter, registry)
    ass21 = next(a for a in r21.report_assessments if a.reportId == "R021")
    assert ass21.verdict == "defect"
    assert ass21.repair in ("type_mismatch", "answer_key")
    assert ass21.edit.field == "answer"
    assert ass21.edit.replace == ["B"]
    assert ass21.final_route == "auto_apply"


def test_r034_unsound_assertion_reason(adapter, registry):
    """R034: Question and solution have contradictory physics; must route to faculty_review."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "R034" in [r.reportId for r in g.reports])
    resp = investigate_question_group(target_group, adapter, registry)

    ass = next(a for a in resp.report_assessments if a.reportId == "R034")
    assert ass.verdict == "defect"
    assert ass.repair == "unsound"
    assert ass.final_route == "faculty_review"
    assert ass.edit is None  # unsound has auto: false in taxonomy


def test_r035_separate_student_claim_from_solution_defect(adapter, registry):
    """R035: Student claim is incorrect (verdict: no_error), while intrinsic solution error is flagged in Quality Findings."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "R035" in [r.reportId for r in g.reports])
    resp = investigate_question_group(target_group, adapter, registry)

    ass = next(a for a in resp.report_assessments if a.reportId == "R035")
    assert ass.verdict == "no_error"
    assert ass.final_route == "no_change"

    # Verify quality finding recorded separately
    quality_findings = resp.verification.quality_findings
    assert len(quality_findings) >= 1
    assert any("insulin" in qf.description.lower() for qf in quality_findings)


def test_r001_r002_r003_shared_investigation_unique_replies(adapter, registry):
    """R001/R002/R003: Share single question investigation, but generate distinct, tailored student replies."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "60f744b3f1b9bc7cc7b4a949" == g.question_id)
    resp = investigate_question_group(target_group, adapter, registry)

    assert len(resp.report_assessments) == 3
    replies = [a.student_reply for a in resp.report_assessments]
    assert len(set(replies)) == 3, "Student replies must be tailored individually"

    for ass in resp.report_assessments:
        assert ass.verdict == "defect"
        assert ass.repair == "answer_key"
        assert ass.edit.replace == "A"
        assert ass.final_route == "auto_apply"


def test_r009_r010_missing_option_never_invented(adapter, registry):
    """R009/R010: Missing Option D must never be invented; routes strictly to faculty_review."""
    groups = group_reports_by_question()
    target_group = next(g for g in groups if "622f08d7b70e4b50e4500a1b" == g.question_id)
    resp = investigate_question_group(target_group, adapter, registry)

    for ass in resp.report_assessments:
        assert ass.verdict == "defect"
        assert ass.repair == "option_repair"
        assert ass.final_route == "faculty_review"


def test_invalid_taxonomy_verdict_fails_closed(registry):
    """Router rejects unauthorized verdict names and enforces taxonomy boundaries."""
    from app.models.investigation import InternalReportAssessment
    with pytest.raises(ValueError, match="Invalid verdict"):
        InternalReportAssessment(
            reportId="R999",
            questionId="60f744b3f1b9bc7cc7b4a949",
            verdict="metadata_issue",  # Disallowed
            suggested_route="auto_apply",
            confidence=0.9,
            evidence="test",
            student_reply="test",
        )


def test_illegal_edit_field_scope_fails_closed(registry):
    """Router blocks proposed edit if field is outside taxonomy.repairs[repair].fields."""
    from app.services.data_loader import load_normalized_questions
    questions = {q.id: q for q in load_normalized_questions()}
    q = questions["617fa18efd53ff1629ed890f"]

    # exam_reference only allows fields: ['question', 'solution']
    illegal_assessment = InternalReportAssessment(
        reportId="R999",
        questionId=q.id,
        verdict="defect",
        repair="exam_reference",
        edit=ProposedEdit(field="answer", find=None, replace="B"),  # Illegal field for exam_reference!
        suggested_route="auto_apply",
        confidence=0.95,
        evidence="test",
        student_reply="test",
        verification_status="passed",
    )

    final_route, errors = calculate_final_route(illegal_assessment, q, registry)
    assert final_route == "faculty_review"
    assert any("outside allowed fields" in err for err in errors)


def test_textual_find_replace_fails_closed_if_not_unique(registry):
    """Router fails closed if find target text does not occur exactly once."""
    from app.services.data_loader import load_normalized_questions
    questions = {q.id: q for q in load_normalized_questions()}
    q = questions["617fa18efd53ff1629ed890f"]

    assessment = InternalReportAssessment(
        reportId="R999",
        questionId=q.id,
        verdict="defect",
        repair="spelling",
        edit=ProposedEdit(field="question", find="non_existent_substring_xyz", replace="replacement"),
        suggested_route="auto_apply",
        confidence=0.95,
        evidence="test",
        student_reply="test",
    )

    final_route, errors = calculate_final_route(assessment, q, registry)
    assert final_route == "faculty_review"
    assert any("occurs 0 times" in err for err in errors)


def test_failed_verification_fails_closed_to_faculty(registry):
    """High-stakes answer key modification without passed verification must route to faculty_review."""
    from app.services.data_loader import load_normalized_questions
    questions = {q.id: q for q in load_normalized_questions()}
    q = questions["60f744b3f1b9bc7cc7b4a949"]

    unverified_assessment = InternalReportAssessment(
        reportId="R999",
        questionId=q.id,
        verdict="defect",
        repair="answer_key",
        edit=ProposedEdit(field="answer", find="C", replace="A"),
        suggested_route="auto_apply",
        confidence=0.95,
        evidence="test",
        student_reply="test",
        verification_status="failed",  # Verification did not pass!
    )

    final_route, errors = calculate_final_route(unverified_assessment, q, registry)
    assert final_route == "faculty_review"
    assert any("requires verification_status 'passed'" in err for err in errors)

