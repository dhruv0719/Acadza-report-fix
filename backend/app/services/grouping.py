from typing import Any, Dict, List, Optional

from app.models.grouping import DuplicateIndicators, QuestionReportGroup
from app.models.precheck import PrecheckFinding
from app.models.question import NormalizedQuestion
from app.models.report import ReportRecord
from app.services.data_loader import load_normalized_questions, load_raw_reports
from app.services.precheck import run_all_prechecks_for_question


def build_duplicate_indicators(reports: List[ReportRecord]) -> DuplicateIndicators:
    """Computes duplicate and relation indicators for a group of reports."""
    report_ids = [r.reportId for r in reports]
    students = [r.studentId for r in reports]
    distinct_students = set(students)
    sources = sorted(list(set(r.source for r in reports)))
    comments = [r.comment for r in reports]
    cleaned_comments = set(c.strip().lower() for c in comments if c)
    identical_comments = len(cleaned_comments) == 1 and len(reports) > 1

    return DuplicateIndicators(
        is_multi_report=len(reports) > 1,
        report_ids=report_ids,
        student_count=len(reports),
        distinct_students_count=len(distinct_students),
        has_duplicate_students=len(distinct_students) < len(students),
        sources=sources,
        identical_comments=identical_comments,
        comments=comments,
    )


def group_reports_by_question(
    questions: Optional[List[NormalizedQuestion]] = None,
    raw_reports: Optional[List[Dict[str, Any]]] = None,
) -> List[QuestionReportGroup]:
    """Groups all reports by canonical MongoDB questionId (_id).
    
    CRITICAL:
    - Canonical identifier is MongoDB _id, never legacy qid.
    - All 44 reports must be assigned to exactly one group.
    - Produces 39 distinct question groups for the reported questions.
    - Preserves pristine report records and normalized question objects.
    """
    if questions is None:
        questions = load_normalized_questions()
    if raw_reports is None:
        raw_reports = load_raw_reports()

    # Index questions strictly by canonical MongoDB _id
    questions_by_id = {q.id: q for q in questions}

    # Group reports by questionId
    reports_by_qid: Dict[str, List[ReportRecord]] = {}
    for r_dict in raw_reports:
        rep = ReportRecord.model_validate(r_dict)
        qid = rep.questionId
        if qid not in questions_by_id:
            raise ValueError(f"Report {rep.reportId} references unknown questionId '{qid}'")
        reports_by_qid.setdefault(qid, []).append(rep)

    # Sort groups deterministically by questionId
    groups: List[QuestionReportGroup] = []
    for qid in sorted(reports_by_qid.keys()):
        rep_list = reports_by_qid[qid]
        # Sort reports inside each group deterministically by reportId
        rep_list.sort(key=lambda r: r.reportId)

        norm_q = questions_by_id[qid]
        findings = run_all_prechecks_for_question(norm_q)
        indicators = build_duplicate_indicators(rep_list)

        group = QuestionReportGroup(
            question_id=qid,
            normalized_question=norm_q,
            reports=rep_list,
            report_count=len(rep_list),
            precheck_findings=findings,
            duplicate_indicators=indicators,
        )
        groups.append(group)

    return groups

