from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.result import ProposedEdit
from app.models.taxonomy import TaxonomyRegistry


# Status Enums allowing explicit uncertainty rather than binary flags
SoundnessStatus = Literal["sound", "unsound", "ambiguous", "insufficient_information"]
AnswerCorrectnessStatus = Literal["correct", "incorrect", "partially_correct", "undetermined", "ambiguous"]
VerificationStatus = Literal["not_required", "pending", "passed", "failed", "inconclusive"]
RouteType = Literal["auto_apply", "faculty_review", "no_change"]
SeverityLevel = Literal["critical", "high", "medium", "low", "info"]


class QualityFinding(BaseModel):
    """Intrinsic question content issue identified independently of student reports."""
    field: str = Field(description="'question', 'solution', 'options', 'answer', 'metadata'")
    issue_type: str = Field(description="e.g. 'solution_factual_error', 'unrendered_markup', 'unsound_question'")
    description: str = Field(description="Precise technical description of the quality defect")
    severity: SeverityLevel = Field(description="Severity: critical | high | medium | low | info")
    independent_of_reports: bool = Field(default=True, description="True if defect was not reported by students")


class BlindSolveOutput(BaseModel):
    """Stage A: Independent academic derivation isolated from stored solution and reports."""
    question_id: str
    derived_answer: Optional[Union[str, List[str]]] = Field(description="Derived answer candidate")
    confidence: float = Field(ge=0.0, le=1.0)
    soundness: SoundnessStatus = Field(description="Assessment of problem soundness without solution bias")
    step_by_step_derivation: str = Field(description="Independent mathematical / scientific derivation")
    assumptions_made: List[str] = Field(default_factory=list)
    missing_data_detected: List[str] = Field(default_factory=list)


class QuestionVerificationOutput(BaseModel):
    """Stage B: Comparison of BlindSolve with stored answer, worked solution, and prechecks."""
    question_id: str
    soundness: SoundnessStatus
    stored_answer_status: AnswerCorrectnessStatus
    verified_answer: Optional[Union[str, List[str]]]
    solution_consistency: Literal["consistent", "contradictory", "unusable", "unrelated"]
    academic_reasoning: str
    quality_findings: List[QualityFinding] = Field(default_factory=list)
    precheck_findings_validated: List[str] = Field(default_factory=list)


class SubmissionResultItem(BaseModel):
    """Strict 9-field assignment contract for results.json.
    
    Contains NO internal metadata, flags, or diagnostic IDs.
    """
    model_config = ConfigDict(extra="forbid")

    reportId: str = Field(description="Report identifier, e.g. R001")
    questionId: str = Field(description="Canonical 24-character MongoDB ObjectId")
    verdict: str = Field(description="One of 7 taxonomy verdicts")
    repair: Optional[str] = Field(default=None, description="One of 18 taxonomy repairs if defect, else None")
    edit: Optional[ProposedEdit] = Field(default=None, description="Surgical change specification")
    route: RouteType = Field(description="Routing: auto_apply | faculty_review | no_change")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(description="Concise justification")
    student_reply: str = Field(description="1-3 empathetic sentences")

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, v: str) -> str:
        registry = TaxonomyRegistry.get_default()
        if not registry.is_valid_verdict(v):
            valid = registry.get_verdict_keys()
            raise ValueError(f"Invalid verdict '{v}'. Must be one of: {valid}")
        return v

    @field_validator("repair")
    @classmethod
    def validate_repair(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        registry = TaxonomyRegistry.get_default()
        if not registry.is_valid_repair(v):
            valid = registry.get_repair_keys()
            raise ValueError(f"Invalid repair '{v}'. Must be one of: {valid}")
        return v


class InternalReportAssessment(BaseModel):
    """Stage C: Rich internal assessment holding security flags, verification traces, and diagnostics."""
    reportId: str
    questionId: str
    verdict: str
    repair: Optional[str] = None
    edit: Optional[ProposedEdit] = None
    suggested_route: RouteType
    final_route: RouteType = "faculty_review"
    confidence: float
    evidence: str
    student_reply: str

    # Internal tracking and security fields (NEVER exported to submission results.json)
    is_prompt_injection: bool = False
    verification_status: VerificationStatus = "not_required"
    verification_evidence: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, v: str) -> str:
        registry = TaxonomyRegistry.get_default()
        if not registry.is_valid_verdict(v):
            valid = registry.get_verdict_keys()
            raise ValueError(f"Invalid verdict '{v}'. Must be one of: {valid}")
        return v

    @field_validator("repair")
    @classmethod
    def validate_repair(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        registry = TaxonomyRegistry.get_default()
        if not registry.is_valid_repair(v):
            valid = registry.get_repair_keys()
            raise ValueError(f"Invalid repair '{v}'. Must be one of: {valid}")
        return v

    def to_submission_item(self) -> SubmissionResultItem:
        """Sanitizes and exports strictly into the 9-field README contract."""
        return SubmissionResultItem(
            reportId=self.reportId,
            questionId=self.questionId,
            verdict=self.verdict,
            repair=self.repair,
            edit=self.edit,
            route=self.final_route,
            confidence=round(self.confidence, 4),
            evidence=self.evidence,
            student_reply=self.student_reply,
        )


class InvestigatorResponse(BaseModel):
    """Complete aggregated output for one question group investigation."""
    question_id: str
    blind_solve: BlindSolveOutput
    verification: QuestionVerificationOutput
    report_assessments: List[InternalReportAssessment]
