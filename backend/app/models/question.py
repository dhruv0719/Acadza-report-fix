from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class ErrorHistoryEntry(BaseModel):
    actor: str = Field(description="Who made the revision, e.g. 'faculty'")
    at: str = Field(description="ISO timestamp of the modification")
    note: str = Field(description="Explanation or note on what changed")
    type: str = Field(description="Type of error corrected, e.g. 'Spelling mistake'")


class ParsedOption(BaseModel):
    key: str = Field(description="Option key, e.g. 'A', 'B', 'C', 'D'")
    html: str = Field(description="Raw HTML segment for this option, including MathML")
    text: str = Field(description="Semantic plain text representation of the option")
    is_blank: bool = Field(default=False, description="True if option has empty/blank text")
    has_mathml: bool = Field(default=False, description="True if option contains MathML")


class RawQuestionPayload(BaseModel):
    question: str
    solution: str
    answer: Any
    quesImages: List[Any] = Field(default_factory=list)
    solutionImages: List[Any] = Field(default_factory=list)


class RawQuestionRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    qid: Optional[str] = None
    questionType: str
    subject: str
    chapter: str
    concept: Optional[str] = None
    subConcept: Optional[str] = None
    level: Optional[Union[int, str]] = None
    error: Optional[int] = 1
    updatedAt: Optional[str] = None
    errorHistory: List[ErrorHistoryEntry] = Field(default_factory=list)
    scq: Optional[RawQuestionPayload] = None
    mcq: Optional[RawQuestionPayload] = None
    integerQuestion: Optional[RawQuestionPayload] = None


class NormalizedQuestion(BaseModel):
    """Normalized representation of a question.
    
    CRITICAL: Preserves original HTML, MathML, raw answer, and full record
    completely intact in raw_question_html, raw_solution_html, and raw_record
    without stripping or loss.
    """
    id: str = Field(description="MongoDB ObjectId string (_id)")
    qid: Optional[str] = Field(default=None, description="Legacy question/paper identifier, if present")
    question_type: str = Field(description="'scq' | 'mcq' | 'integerQuestion'")
    subject: str
    chapter: str
    concept: Optional[str] = None
    sub_concept: Optional[str] = None
    level: Optional[Union[int, str]] = None
    updated_at: Optional[str] = None
    error_flag: int = 1
    error_history: List[ErrorHistoryEntry] = Field(default_factory=list)

    # Pristine originals - NEVER discarded or mutated
    raw_question_html: str = Field(description="Pristine question HTML + MathML as stored in production")
    raw_solution_html: str = Field(description="Pristine solution HTML + MathML as stored in production")

    # Extracted structures (DOM-derived)
    stem_html: str = Field(description="Question stem HTML prior to options (or full HTML if integer)")
    stem_text: str = Field(description="Semantic plain text representation of question stem (MathML converted)")
    solution_text: str = Field(description="Semantic plain text representation of solution (MathML converted)")
    options: List[ParsedOption] = Field(default_factory=list, description="Parsed options list")
    
    # Answers (raw preserved, anomalies recorded, interpreted candidate provided)
    raw_answer: Any = Field(description="Original unmutated answer field from raw JSON")
    normalized_answer: Union[str, List[str]] = Field(description="Interpreted answer candidate")
    answer_anomalies: List[str] = Field(default_factory=list, description="Anomalies detected in raw answer")
    parser_warnings: List[str] = Field(default_factory=list, description="Warnings generated during normalization")

    # Images & Media
    ques_images: List[Any] = Field(default_factory=list)
    solution_images: List[Any] = Field(default_factory=list)

    # Diagnostic metadata
    has_mathml: bool = Field(default=False, description="Whether question or solution contains MathML")
    has_figure_reference: bool = Field(default=False, description="Whether text references a figure/diagram")
    report_ids: List[str] = Field(default_factory=list, description="Associated report IDs from reports.json")

    # Complete original document for zero-loss recovery
    raw_record: Dict[str, Any] = Field(default_factory=dict, description="Untouched raw dictionary")
