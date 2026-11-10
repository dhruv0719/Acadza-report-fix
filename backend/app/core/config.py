from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to repository root (d:\acadza-report-fix)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Project-relative data paths
    DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
    TAXONOMY_PATH: Path = PROJECT_ROOT / "data" / "raw" / "taxonomy.json"
    QUESTIONS_PATH: Path = PROJECT_ROOT / "data" / "raw" / "questions.json"
    REPORTS_PATH: Path = PROJECT_ROOT / "data" / "raw" / "reports.json"
    RESULTS_PATH: Path = PROJECT_ROOT / "results.json"
    QUALITY_FINDINGS_PATH: Path = PROJECT_ROOT / "data" / "question_quality_findings.json"
    UNREPORTED_AUDIT_PATH: Path = PROJECT_ROOT / "data" / "unreported_question_audit.json"
    TELEMETRY_LOG_PATH: Path = PROJECT_ROOT / "data" / "llm_usage_log.json"
    CHECKPOINTS_PATH: Path = PROJECT_ROOT / "data" / "investigation_checkpoints.json"
    PRECHECK_FINDINGS_PATH: Path = PROJECT_ROOT / "data" / "precheck_findings.json"
    PRECHECK_SUMMARY_PATH: Path = PROJECT_ROOT / "data" / "precheck_summary.json"
    FACULTY_REVIEWS_PATH: Path = PROJECT_ROOT / "data" / "faculty_reviews.json"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
