from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.question import NormalizedQuestion
from app.models.report import ReportGroup, ReportRecord
from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import (
    get_questions_map,
    get_report_groups,
    load_normalized_questions,
    load_reports,
)

router = APIRouter()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    registry = TaxonomyRegistry.get_default()
    questions = load_normalized_questions()
    reports = load_reports()
    return {
        "status": "healthy",
        "questions_count": len(questions),
        "reports_count": len(reports),
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
    if question_type:
        questions = [q for q in questions if q.question_type == question_type]
    if reported_only:
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
    if question_id:
        reports = [r for r in reports if r.questionId == question_id]
    if source:
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

