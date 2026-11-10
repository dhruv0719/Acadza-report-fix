import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.models.question import NormalizedQuestion
from app.models.report import ReportGroup, ReportRecord
from app.models.taxonomy import TaxonomyRegistry
from app.services.normalizer import normalize_question


def load_raw_questions(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.QUESTIONS_PATH
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_raw_reports(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.REPORTS_PATH
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_taxonomy(path: Optional[Path] = None) -> TaxonomyRegistry:
    file_path = path or settings.TAXONOMY_PATH
    return TaxonomyRegistry(file_path)


def load_reports(path: Optional[Path] = None) -> List[ReportRecord]:
    raw_reports = load_raw_reports(path)
    return [ReportRecord.model_validate(r) for r in raw_reports]


def get_report_groups(path: Optional[Path] = None) -> Dict[str, ReportGroup]:
    reports = load_reports(path)
    grouped: Dict[str, List[ReportRecord]] = defaultdict(list)
    for r in reports:
        grouped[r.questionId].append(r)

    result: Dict[str, ReportGroup] = {}
    for qid, reps in grouped.items():
        result[qid] = ReportGroup(
            questionId=qid,
            report_count=len(reps),
            reports=reps,
            sources=list(set(r.source for r in reps)),
            comments=[r.comment for r in reps],
        )
    return result


def load_normalized_questions(
    questions_path: Optional[Path] = None,
    reports_path: Optional[Path] = None,
) -> List[NormalizedQuestion]:
    raw_questions = load_raw_questions(questions_path)
    report_groups = get_report_groups(reports_path)

    normalized: List[NormalizedQuestion] = []
    for raw in raw_questions:
        qid = raw.get("_id")
        rep_group = report_groups.get(qid)
        rep_ids = [r.reportId for r in rep_group.reports] if rep_group else []
        norm = normalize_question(raw, report_ids=rep_ids)
        normalized.append(norm)

    return normalized


def get_questions_map(
    questions_path: Optional[Path] = None,
    reports_path: Optional[Path] = None,
) -> Dict[str, NormalizedQuestion]:
    questions = load_normalized_questions(questions_path, reports_path)
    return {q.id: q for q in questions}


def load_results(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.RESULTS_PATH
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_quality_findings(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.QUALITY_FINDINGS_PATH
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_unreported_audit(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.UNREPORTED_AUDIT_PATH
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_telemetry(path: Optional[Path] = None) -> List[Dict]:
    file_path = path or settings.TELEMETRY_LOG_PATH
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_checkpoints(path: Optional[Path] = None) -> Dict[str, Any]:
    file_path = path or settings.CHECKPOINTS_PATH
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_precheck_findings(path: Optional[Path] = None) -> Dict[str, Any]:
    file_path = path or settings.PRECHECK_FINDINGS_PATH
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_precheck_summary(path: Optional[Path] = None) -> Dict[str, Any]:
    file_path = path or settings.PRECHECK_SUMMARY_PATH
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_faculty_reviews(path: Optional[Path] = None) -> Dict[str, Any]:
    file_path = path or settings.FACULTY_REVIEWS_PATH
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_faculty_review(
    report_id: str,
    review_data: Dict[str, Any],
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    file_path = path or settings.FACULTY_REVIEWS_PATH
    reviews = load_faculty_reviews(file_path)
    reviews[report_id] = review_data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2)
    return reviews

