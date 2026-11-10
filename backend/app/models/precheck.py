from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


SeverityLevel = Literal["critical", "high", "medium", "low", "info"]


class PrecheckFinding(BaseModel):
    """Deterministic precheck finding on a question.
    
    CRITICAL: Keep detections separate from final verdicts.
    A finding flags a suspicious structure or verified rule trigger,
    leaving defect confirmation and repair decisions to subsequent triage.
    """
    question_id: str = Field(description="Canonical MongoDB ObjectId (_id)")
    check_id: str = Field(description="Deterministic check identifier, e.g. 'MISSING_OPTIONS'")
    severity: SeverityLevel = Field(description="Severity: critical | high | medium | low | info")
    evidence: str = Field(description="Clear explanation and evidence of what was detected")
    source_field: str = Field(description="Field where defect was detected (e.g. 'options', 'answer')")
    requires_investigation: bool = Field(default=True, description="Whether manual/LLM investigation is needed")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured metadata for downstream triage")

