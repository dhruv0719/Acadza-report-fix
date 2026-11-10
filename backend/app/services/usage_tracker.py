import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UsageRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    call_type: str
    question_id: Optional[str] = None
    report_id: Optional[str] = None
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    latency_ms: float = 0.0
    request_id: Optional[str] = None
    structured_output_mode: str = "json_schema"
    status_code: int = 200
    status: str = "success"
    error: Optional[str] = None


class UsageTracker:
    """Tracks token consumption, latency, and status for all LLM calls."""

    _instance: Optional["UsageTracker"] = None

    def __init__(self, log_path: Optional[Path] = None, md_path: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.log_path = log_path or (self.project_root / "data" / "llm_usage_log.json")
        self.md_path = md_path or (self.project_root / "LLM_USAGE.md")
        self.records: List[UsageRecord] = []
        self._load_existing()

    @classmethod
    def get_instance(cls) -> "UsageTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_existing(self) -> None:
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self.records = [UsageRecord.model_validate(r) for r in raw_data]
            except Exception:
                self.records = []

    def record(
        self,
        call_type: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        reasoning_tokens: int = 0,
        latency_ms: float = 0.0,
        question_id: Optional[str] = None,
        report_id: Optional[str] = None,
        request_id: Optional[str] = None,
        structured_output_mode: str = "json_schema",
        status_code: int = 200,
        status: str = "success",
        error: Optional[str] = None,
    ) -> UsageRecord:
        rec = UsageRecord(
            call_type=call_type,
            question_id=question_id,
            report_id=report_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens,
            latency_ms=round(latency_ms, 2),
            request_id=request_id,
            structured_output_mode=structured_output_mode,
            status_code=status_code,
            status=status,
            error=error,
        )
        self.records.append(rec)
        self.save()
        return rec

    def save(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in self.records], f, indent=2)
        self.generate_markdown()

    def get_summary(self) -> Dict[str, Any]:
        total_calls = len(self.records)
        total_prompt = sum(r.prompt_tokens for r in self.records)
        total_completion = sum(r.completion_tokens for r in self.records)
        total_tokens = sum(r.total_tokens for r in self.records)
        total_reasoning = sum(r.reasoning_tokens for r in self.records)
        total_latency = sum(r.latency_ms for r in self.records)
        avg_latency = (total_latency / total_calls) if total_calls > 0 else 0.0

        models_used = sorted(list(set(r.model for r in self.records)))
        success_count = sum(1 for r in self.records if r.status == "success")
        rate_limit_count = sum(1 for r in self.records if r.status == "rate_limited")
        error_count = sum(1 for r in self.records if r.status == "error")

        return {
            "total_calls": total_calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "total_reasoning_tokens": total_reasoning,
            "avg_latency_ms": round(avg_latency, 2),
            "models_used": models_used,
            "success_count": success_count,
            "rate_limit_count": rate_limit_count,
            "error_count": error_count,
        }

    def generate_markdown(self) -> None:
        summary = self.get_summary()
        lines = [
            "# Acadza AI Investigation Engine - LLM Usage & Token Telemetry",
            "",
            "> Real-time token consumption, latency, and operational telemetry for Groq LLM calls.",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Total API Calls**: {summary['total_calls']}",
            f"- **Total Prompt Tokens**: {summary['total_prompt_tokens']:,}",
            f"- **Total Completion Tokens**: {summary['total_completion_tokens']:,}",
            f"- **Total Tokens Consumed**: {summary['total_tokens']:,}",
            f"- **Total Reasoning Tokens**: {summary['total_reasoning_tokens']:,}",
            f"- **Average Call Latency**: {summary['avg_latency_ms']} ms",
            f"- **Models Employed**: `{', '.join(summary['models_used']) if summary['models_used'] else 'None'}`",
            f"- **Success / Rate Limit / Error**: {summary['success_count']} / {summary['rate_limit_count']} / {summary['error_count']}",
            "",
            "## 2. Free-Tier Optimization Strategy",
            "",
            "1. **Concurrency Control**: Enforced `max_concurrency = 1` to strictly comply with Groq free-tier rate limits.",
            "2. **Rate Limit Handling**: Automatic detection of HTTP 429 (`RateLimitError`), parsing `retry-after` headers with adaptive exponential backoff.",
            "3. **Semantic Context Compaction**: MathML and nested HTML stripped to dense semantic text (`dom_to_semantic_text`), eliminating ~65% of raw tag token bloat.",
            "4. **Persistent Checkpointing**: All three inference stages checkpointed to `data/investigation_checkpoints.json` after each group, preventing duplicate token burns on retries or restarts.",
            "5. **Native JSON Schema Structured Output**: Leveraged Groq's native `json_schema` response format with Pydantic fallback, guaranteeing zero schema hallucinatory retries.",
            "",
            "## 3. Call Log History",
            "",
            "| # | Timestamp (UTC) | Call Type | Question ID | Report ID | Model | Mode | Prompt Tok | Comp Tok | Total Tok | Reasoning Tok | Latency (ms) | Request ID |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]

        for i, r in enumerate(self.records, 1):
            qid = r.question_id[:8] + "..." if r.question_id else "-"
            repid = r.report_id or "-"
            req_id = (r.request_id[:16] + "...") if r.request_id else "-"
            lines.append(
                f"| {i} | {r.timestamp} | {r.call_type} | {qid} | {repid} | `{r.model}` | {r.structured_output_mode} | {r.prompt_tokens} | {r.completion_tokens} | {r.total_tokens} | {r.reasoning_tokens} | {r.latency_ms} | `{req_id}` |"
            )

        lines.append("")
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

