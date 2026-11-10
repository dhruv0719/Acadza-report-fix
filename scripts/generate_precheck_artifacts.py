import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import settings
from app.services.data_loader import load_normalized_questions, load_raw_reports
from app.services.grouping import group_reports_by_question
from app.services.precheck import run_all_prechecks


def generate_artifacts():
    print("Loading normalized questions and raw reports...")
    questions = load_normalized_questions()
    reports = load_raw_reports()

    # 1. Run deterministic prechecks on all 43 questions
    findings = run_all_prechecks(questions)
    print(f"Detected {len(findings)} precheck findings across {len(questions)} questions.")

    # 2. Group all 44 reports by questionId
    groups = group_reports_by_question(questions, reports)
    print(f"Formed {len(groups)} question report groups containing {sum(g.report_count for g in groups)} reports.")

    # 3. Build summary
    by_check_id = Counter(f.check_id for f in findings)
    by_severity = Counter(f.severity for f in findings)
    questions_with_findings = sorted(list(set(f.question_id for f in findings)))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions_processed": len(questions),
        "total_reports_processed": len(reports),
        "distinct_question_groups": len(groups),
        "total_findings": len(findings),
        "questions_with_findings_count": len(questions_with_findings),
        "questions_clean_count": len(questions) - len(questions_with_findings),
        "multi_report_groups_count": sum(1 for g in groups if g.duplicate_indicators.is_multi_report),
        "findings_by_check_id": dict(sorted(by_check_id.items())),
        "findings_by_severity": dict(sorted(by_severity.items())),
        "findings_requiring_investigation": sum(1 for f in findings if f.requires_investigation),
        "questions_with_findings_ids": questions_with_findings,
    }

    # 4. Save artifacts to data/
    data_dir = settings.DATA_RAW_DIR.parent

    # A: precheck_findings.json
    findings_path = data_dir / "precheck_findings.json"
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump([f.model_dump() for f in findings], f, indent=2, ensure_ascii=False)
    print(f"Wrote precheck findings to {findings_path}")

    # B: report_groups.json
    groups_path = data_dir / "report_groups.json"
    with open(groups_path, "w", encoding="utf-8") as f:
        json.dump([g.model_dump() for g in groups], f, indent=2, ensure_ascii=False)
    print(f"Wrote report groups to {groups_path}")

    # C: precheck_summary.json
    summary_path = data_dir / "precheck_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote precheck summary to {summary_path}")

    print("\nGeneration completed successfully.")


if __name__ == "__main__":
    generate_artifacts()

