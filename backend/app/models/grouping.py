from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.precheck import PrecheckFinding
from app.models.question import NormalizedQuestion
from app.models.report import ReportRecord


class DuplicateIndicators(BaseModel):
    """Indicators for duplicate, repeated, or related reports in a question group."""
    is_multi_report: bool = Field(description="True if more than 1 report exists for this question")
    report_ids: List[str] = Field(default_factory=list, description="All report IDs in this group")
    student_count: int = Field(description="Total student reports")
    distinct_students_count: int = Field(description="Count of distinct reporting students")
    has_duplicate_students: bool = Field(default=False, description="True if same student reported multiple times")
    sources: List[str] = Field(default_factory=list, description="Unique source platforms (android, ios, web)")
    identical_comments: bool = Field(default=False, description="True if all comments in this group are identical")
    comments: List[str] = Field(default_factory=list, description="All student comments for this question")


class QuestionReportGroup(BaseModel):
    """Question report group aggregating all reports and precheck findings by canonical questionId."""
    question_id: str = Field(description="Canonical MongoDB ObjectId (_id)")
    normalized_question: NormalizedQuestion = Field(description="Fully normalized question record")
    reports: List[ReportRecord] = Field(description="Original report records associated with this question")
    report_count: int = Field(description="Total count of reports in this group")
    precheck_findings: List[PrecheckFinding] = Field(default_factory=list, description="Precheck findings detected for this question")
    duplicate_indicators: DuplicateIndicators = Field(description="Duplicate and relation indicators")

