from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ReportRecord(BaseModel):
    reportId: str = Field(description="Unique report identifier, e.g. R001")
    questionId: str = Field(description="Referenced question ID")
    studentId: str = Field(description="Student identifier, e.g. stu_cd48eb56")
    source: Literal["android", "ios", "web"] = Field(description="Client source platform")
    reportedAt: str = Field(description="ISO timestamp of report submission")
    comment: str = Field(description="Raw text entered by student")


class ReportGroup(BaseModel):
    questionId: str
    report_count: int
    reports: List[ReportRecord]
    sources: List[str]
    comments: List[str]

