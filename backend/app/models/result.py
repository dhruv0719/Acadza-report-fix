from typing import Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

from app.models.taxonomy import TaxonomyRegistry


class ProposedEdit(BaseModel):
    field: str = Field(description="Target field name, e.g. 'answer', 'question', 'solution'")
    find: Optional[str] = Field(default=None, description="Substring to find, if surgical string replacement")
    replace: Any = Field(description="Replacement string, value, or new answer")


class ResultItem(BaseModel):
    """Result contract matching README Part 3 specification for results.json.
    
    Validates verdicts and repairs against taxonomy.json programmatically.
    """
    reportId: str = Field(description="Report identifier, e.g. R001")
    questionId: str = Field(description="24-char question ID")
    verdict: str = Field(description="Verdict key from taxonomy.json verdicts")
    repair: Optional[str] = Field(default=None, description="Repair key from taxonomy.json repairs if defect")
    edit: Optional[ProposedEdit] = Field(default=None, description="Surgical edit specification")
    route: Literal["auto_apply", "faculty_review", "no_change"] = Field(
        description="Routing destination for this triage action"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    evidence: str = Field(description="Short evidence explaining the reasoning")
    student_reply: str = Field(description="1-3 sentence empathetic reply to student")

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

    def validate_repair_field_scope(self) -> bool:
        """Validates that proposed edit touches only fields allowed by the repair type."""
        if not self.repair or not self.edit:
            return True
        registry = TaxonomyRegistry.get_default()
        allowed = registry.get_repair_fields(self.repair)
        return self.edit.field in allowed

