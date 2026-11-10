import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import settings
from app.models.investigation import SubmissionResultItem
from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import load_raw_reports
from app.services.grouping import group_reports_by_question
from app.services.investigator import investigate_all_groups
from app.services.llm_adapter import LLMAdapter


def execute_full_investigation():
    print("Executing Full AI Investigation across all 39 question groups...")
    registry = TaxonomyRegistry.get_default()
    adapter = LLMAdapter()  # Uses configured provider or deterministic solver

    all_groups = group_reports_by_question()
    print(f"Loaded {len(all_groups)} question groups covering 44 reports.\n")

    responses, submission_items, quality_findings = investigate_all_groups(all_groups, adapter, registry)

    print(f"Investigation complete: {len(responses)} group responses generated.")
    print(f"Total report assessments: {len(submission_items)}")
    print(f"Total intrinsic quality findings identified: {len(quality_findings)}\n")

    # Validation checks against assignment contract
    assert len(submission_items) == 44, f"Expected 44 items, got {len(submission_items)}"
    report_ids = [item.reportId for item in submission_items]
    assert len(set(report_ids)) == 44, "Duplicate report IDs in submission items!"

    raw_reports = load_raw_reports()
    expected_map = {r["reportId"]: r["questionId"] for r in raw_reports}
    for item in submission_items:
        assert item.questionId == expected_map[item.reportId], (
            f"Question ID mismatch on {item.reportId}: expected {expected_map[item.reportId]}, got {item.questionId}"
        )
        # Check verdict
        assert registry.is_valid_verdict(item.verdict), f"Invalid verdict '{item.verdict}'"
        # Check repair
        if item.verdict == "defect":
            assert item.repair is not None and registry.is_valid_repair(item.repair), f"Invalid repair '{item.repair}'"
        else:
            assert item.repair is None, f"Non-defect report {item.reportId} has repair '{item.repair}'"
            assert item.edit is None, f"Non-defect report {item.reportId} has edit"
            assert item.route == "no_change", f"Non-defect report {item.reportId} route must be no_change, got {item.route}"

    print("All 44 submission items validated against taxonomy and assignment contract!\n")

    # Serialize to JSON (strictly 9 fields)
    results_data = [item.model_dump(exclude_none=False) for item in submission_items]
    # For items where repair/edit is None, clean format
    cleaned_results = []
    for item in results_data:
        cleaned_item = {
            "reportId": item["reportId"],
            "questionId": item["questionId"],
            "verdict": item["verdict"],
            "repair": item["repair"],
            "edit": item["edit"],
            "route": item["route"],
            "confidence": item["confidence"],
            "evidence": item["evidence"],
            "student_reply": item["student_reply"],
        }
        cleaned_results.append(cleaned_item)

    # Save to data/results.json and root results.json
    data_results_path = settings.DATA_RAW_DIR.parent / "results.json"
    with open(data_results_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
    print(f"Wrote submission results to {data_results_path}")

    root_results_path = settings.RESULTS_PATH
    with open(root_results_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
    print(f"Wrote submission results to {root_results_path}")

    # Save quality findings artifact
    quality_path = settings.DATA_RAW_DIR.parent / "question_quality_findings.json"
    with open(quality_path, "w", encoding="utf-8") as f:
        json.dump([qf.model_dump() for qf in quality_findings], f, indent=2, ensure_ascii=False)
    print(f"Wrote quality findings artifact to {quality_path}\n")

    # Summary Breakdown
    from collections import Counter
    verdicts_count = Counter(item["verdict"] for item in cleaned_results)
    repairs_count = Counter(item["repair"] for item in cleaned_results if item["repair"])
    routes_count = Counter(item["route"] for item in cleaned_results)

    print("=== SUMMARY METRICS ===")
    print("Verdicts:")
    for v, c in verdicts_count.items():
        print(f"  - {v}: {c}")
    print("\nRepairs (for defects):")
    for r, c in repairs_count.items():
        print(f"  - {r}: {c}")
    print("\nRoutes:")
    for r, c in routes_count.items():
        print(f"  - {r}: {c}")


if __name__ == "__main__":
    execute_full_investigation()

