import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.models.taxonomy import TaxonomyRegistry
from app.services.data_loader import load_normalized_questions, load_raw_reports
from app.services.grouping import group_reports_by_question
from app.services.investigator import investigate_question_group
from app.services.llm_adapter import LLMAdapter


def run_critical_dry_run():
    print("Initializing dry-run on critical regression cases...\n")
    registry = TaxonomyRegistry.get_default()
    adapter = LLMAdapter()  # Uses deterministic mock by default

    all_groups = group_reports_by_question()
    groups_by_qid = {g.question_id: g for g in all_groups}

    target_reports = ["R004", "R027", "R017", "R020", "R021", "R034", "R035", "R001", "R002", "R003", "R009", "R010"]
    
    # Identify unique question groups for these reports
    raw_reports = load_raw_reports()
    rep_map = {r["reportId"]: r["questionId"] for r in raw_reports}
    
    target_qids = []
    for rid in target_reports:
        qid = rep_map[rid]
        if qid not in target_qids:
            target_qids.append(qid)

    print(f"Targeting {len(target_reports)} reports across {len(target_qids)} question groups.\n")

    for qid in target_qids:
        group = groups_by_qid[qid]
        res = investigate_question_group(group, adapter, registry)

        print(f"================================================================================")
        print(f"Question Group: {qid} ({group.normalized_question.question_type})")
        print(f"Blind Solve: Answer={res.blind_solve.derived_answer}, Soundness={res.blind_solve.soundness}")
        print(f"Verification: StoredStatus={res.verification.stored_answer_status}, Consistency={res.verification.solution_consistency}")
        if res.verification.quality_findings:
            print(f"Quality Findings: {[qf.description for qf in res.verification.quality_findings]}")
        
        print("\nReport Assessments:")
        for ass in res.report_assessments:
            if ass.reportId in target_reports:
                print(f"  [{ass.reportId}] Verdict: {ass.verdict} | Repair: {ass.repair} | Route: {ass.final_route}")
                print(f"      Proposed Edit: {ass.edit.model_dump() if ass.edit else None}")
                print(f"      Verification Status: {ass.verification_status}")
                print(f"      Evidence: {ass.evidence}")
                print(f"      Student Reply: {ass.student_reply}")
                print(f"      Security (Prompt Injection): {ass.is_prompt_injection}")
                if ass.validation_errors:
                    print(f"      Route Validation Errors: {ass.validation_errors}")
                print()

if __name__ == "__main__":
    run_critical_dry_run()

