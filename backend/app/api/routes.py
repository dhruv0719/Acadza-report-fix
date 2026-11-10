import datetime
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.question import NormalizedQuestion
from app.models.report import ReportGroup, ReportRecord
from app.models.result import ProposedEdit, ResultItem
from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import (
    get_questions_map,
    get_report_groups,
    load_checkpoints,
    load_faculty_reviews,
    load_normalized_questions,
    load_precheck_findings,
    load_precheck_summary,
    load_quality_findings,
    load_reports,
    load_results,
    load_telemetry,
    load_unreported_audit,
    save_faculty_review,
)

router = APIRouter()


class FacultyReviewRequest(BaseModel):
    action: Literal["approve", "reject", "modify"]
    reviewer_notes: Optional[str] = None
    modified_edit: Optional[ProposedEdit] = None
    custom_reply: Optional[str] = None
    reviewer_name: Optional[str] = "Faculty Reviewer"


class FacultyReviewResponse(BaseModel):
    report_id: str
    action: str
    reviewer_name: str
    reviewed_at: str
    reviewer_notes: Optional[str] = None
    modified_edit: Optional[ProposedEdit] = None
    custom_reply: Optional[str] = None
    status: str


@router.get("/health")
def health_check() -> Dict[str, Any]:
    registry = TaxonomyRegistry.get_default()
    questions = load_normalized_questions()
    reports = load_reports()
    results = load_results()
    return {
        "status": "healthy",
        "questions_count": len(questions),
        "reports_count": len(reports),
        "results_count": len(results),
        "verdicts_count": len(registry.get_verdicts()),
        "repairs_count": len(registry.get_repairs()),
    }


@router.get("/taxonomy")
def get_taxonomy() -> Dict[str, Any]:
    registry = TaxonomyRegistry.get_default()
    return {
        "verdicts": registry.get_verdicts(),
        "repairs": {
            k: v.model_dump() for k, v in registry.get_repairs().items()
        },
    }


@router.get("/questions", response_model=List[NormalizedQuestion])
def list_questions(
    question_type: Optional[str] = Query(default=None, description="Filter by scq, mcq, integerQuestion"),
    reported_only: bool = Query(default=False, description="Filter only questions with at least 1 student report"),
) -> List[NormalizedQuestion]:
    questions = load_normalized_questions()
    if isinstance(question_type, str) and question_type:
        questions = [q for q in questions if q.question_type == question_type]
    if isinstance(reported_only, bool) and reported_only:
        questions = [q for q in questions if len(q.report_ids) > 0]
    return questions


@router.get("/questions/{question_id}", response_model=NormalizedQuestion)
def get_question(question_id: str) -> NormalizedQuestion:
    qmap = get_questions_map()
    if question_id not in qmap:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return qmap[question_id]


@router.get("/reports", response_model=List[ReportRecord])
def list_reports(
    question_id: Optional[str] = Query(default=None, description="Filter reports by question ID"),
    source: Optional[str] = Query(default=None, description="Filter by source: android, ios, web"),
) -> List[ReportRecord]:
    reports = load_reports()
    if isinstance(question_id, str) and question_id:
        reports = [r for r in reports if r.questionId == question_id]
    if isinstance(source, str) and source:
        reports = [r for r in reports if r.source == source]
    return reports


@router.get("/reports/grouped", response_model=Dict[str, ReportGroup])
def list_grouped_reports() -> Dict[str, ReportGroup]:
    return get_report_groups()


@router.get("/reports/{report_id}", response_model=ReportRecord)
def get_report(report_id: str) -> ReportRecord:
    reports = load_reports()
    for r in reports:
        if r.reportId == report_id:
            return r
    raise HTTPException(status_code=404, detail=f"Report {report_id} not found")


@router.get("/results", response_model=List[ResultItem])
def list_results(
    route: Optional[str] = Query(default=None, description="Filter by route: auto_apply, faculty_review, no_change"),
    verdict: Optional[str] = Query(default=None, description="Filter by verdict"),
    question_id: Optional[str] = Query(default=None, description="Filter by questionId"),
) -> List[ResultItem]:
    raw_results = load_results()
    items = [ResultItem.model_validate(r) for r in raw_results]
    if isinstance(route, str) and route:
        items = [i for i in items if i.route == route]
    if isinstance(verdict, str) and verdict:
        items = [i for i in items if i.verdict == verdict]
    if isinstance(question_id, str) and question_id:
        items = [i for i in items if i.questionId == question_id]
    return items


@router.get("/results/{report_id}", response_model=ResultItem)
def get_result(report_id: str) -> ResultItem:
    raw_results = load_results()
    for r in raw_results:
        if r.get("reportId") == report_id:
            return ResultItem.model_validate(r)
    raise HTTPException(status_code=404, detail=f"Result for report {report_id} not found")


@router.get("/quality-findings")
def get_quality_findings() -> List[Dict[str, Any]]:
    return load_quality_findings()


@router.get("/unreported-audit")
def get_unreported_audit() -> List[Dict[str, Any]]:
    return load_unreported_audit()


@router.get("/telemetry")
def get_telemetry() -> Dict[str, Any]:
    logs = load_telemetry()
    total_calls = len(logs)
    total_prompt_tokens = sum(l.get("prompt_tokens", 0) for l in logs)
    total_completion_tokens = sum(l.get("completion_tokens", 0) for l in logs)
    total_reasoning_tokens = sum(l.get("reasoning_tokens", 0) for l in logs)
    total_tokens = sum(l.get("total_tokens", 0) for l in logs)
    total_latency_ms = sum(l.get("latency_ms", 0) for l in logs)

    return {
        "summary": {
            "total_calls": total_calls,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_reasoning_tokens": total_reasoning_tokens,
            "total_tokens": total_tokens,
            "total_latency_seconds": round(total_latency_ms / 1000.0, 2),
            "average_latency_ms": round(total_latency_ms / total_calls, 1) if total_calls else 0,
            "primary_model": "openai/gpt-oss-120b",
            "provider": "Groq",
        },
        "logs": logs,
    }


@router.get("/checkpoints")
def get_checkpoints() -> Dict[str, Any]:
    return load_checkpoints()


@router.get("/checkpoints/{question_id}")
def get_question_checkpoint(question_id: str) -> Dict[str, Any]:
    checkpoints = load_checkpoints()
    if question_id not in checkpoints:
        raise HTTPException(status_code=404, detail=f"Checkpoint for question {question_id} not found")
    return checkpoints[question_id]


@router.get("/precheck")
def get_precheck() -> Dict[str, Any]:
    return {
        "summary": load_precheck_summary(),
        "findings": load_precheck_findings(),
    }


@router.get("/faculty-reviews")
def get_all_faculty_reviews() -> Dict[str, Any]:
    return load_faculty_reviews()


@router.post("/review/{report_id}", response_model=FacultyReviewResponse)
def submit_faculty_review(report_id: str, review: FacultyReviewRequest) -> FacultyReviewResponse:
    # Verify report exists
    results = load_results()
    matching_result = next((r for r in results if r.get("reportId") == report_id), None)
    if not matching_result:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found in results")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "report_id": report_id,
        "action": review.action,
        "reviewer_name": review.reviewer_name or "Faculty Reviewer",
        "reviewed_at": now_iso,
        "reviewer_notes": review.reviewer_notes,
        "modified_edit": review.modified_edit.model_dump() if review.modified_edit else None,
        "custom_reply": review.custom_reply,
        "status": "approved" if review.action == "approve" else ("rejected" if review.action == "reject" else "modified"),
    }
    save_faculty_review(report_id, record)
    return FacultyReviewResponse(**record)

