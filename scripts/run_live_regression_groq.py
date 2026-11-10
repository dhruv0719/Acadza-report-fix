import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import dotenv
dotenv.load_dotenv(PROJECT_ROOT / ".env")

from app.models.taxonomy import TaxonomyRegistry
from app.services.checkpoint_manager import CheckpointManager
from app.services.grouping import group_reports_by_question
from app.services.investigator import (
    assess_reports_for_group,
    blind_solve_question,
    verify_question_and_solution,
)
from app.services.llm_adapter import LLMAdapter, LLMConfig
from app.services.usage_tracker import UsageTracker
from app.models.investigation import InvestigatorResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_regression_groq")


def run_live_regression():
    logger.info("================================================================================")
    logger.info("ACADZA AI INVESTIGATION ENGINE: LIVE GROQ REGRESSION CASES (R027, R034, R035)")
    logger.info("================================================================================")

    # 1. Verify credentials and configuration
    config = LLMConfig(provider="groq")
    if not config.groq_api_key:
        logger.error("GROQ_API_KEY not found in .env. Cannot perform live Groq regression.")
        sys.exit(1)

    logger.info(f"Target LLM Provider : {config.provider}")
    logger.info(f"Primary Model ID    : {config.model}")
    logger.info(f"Fallback Model ID   : {config.fallback_model}")
    logger.info(f"Temperature         : {config.temperature}")
    logger.info(f"Reasoning Effort    : {config.reasoning_effort}")
    logger.info(f"Structured Output   : {config.structured_output}")
    logger.info("GROQ_API_KEY is present and securely loaded.")

    adapter = LLMAdapter(config=config)
    registry = TaxonomyRegistry.get_default()
    tracker = UsageTracker.get_instance()
    checkpoint_mgr = CheckpointManager()

    # Load grouped questions
    all_groups = group_reports_by_question()
    q_map = {g.question_id: g for g in all_groups}

    cases = [
        {"rid": "R027", "qid": "6062ec84518e9535e120c422", "title": "CASE A: R027 (Prompt Injection Attack)"},
        {"rid": "R034", "qid": "695ee00b88d7701e561aabc5", "title": "CASE B: R034 (Unsound Assertion-Reason)"},
        {"rid": "R035", "qid": "66fe9dbe22132e5a70a3e579", "title": "CASE C: R035 (Independent Evaluation & Solution Defect)"},
    ]

    executed_results = {}

    for idx, case in enumerate(cases, 1):
        rid = case["rid"]
        qid = case["qid"]
        title = case["title"]

        logger.info(f"\n{'=' * 80}")
        logger.info(f"STARTING {title}")
        logger.info(f"Question ID: {qid} | Report ID: {rid}")
        logger.info(f"{'=' * 80}")

        target_group = q_map.get(qid)
        if not target_group:
            logger.error(f"Question group for {qid} not found!")
            sys.exit(1)

        q = target_group.normalized_question
        rep = next((r for r in target_group.reports if r.reportId == rid), None)
        logger.info(f"Subject: {q.subject} | Chapter: {q.chapter} | Type: {q.question_type}")
        logger.info(f"Question Stem: {q.stem_text[:120]}...")
        logger.info(f"Stored Answer: {q.raw_answer}")
        logger.info(f"Student Comment: '{rep.comment}'")

        call_count_start = len(tracker.records)

        # Stage A: Truly Isolated Blind Solve
        logger.info(f"\n--- [STAGE A: BLIND SOLVE ({rid})] ---")
        t0_a = time.time()
        blind_solve = blind_solve_question(target_group, adapter)
        lat_a = (time.time() - t0_a) * 1000.0
        logger.info(f"Stage A Latency: {lat_a:.2f} ms")
        logger.info(f"Soundness: {blind_solve.soundness} | Derived Answer: {blind_solve.derived_answer}")
        logger.info(f"Derivation:\n{blind_solve.step_by_step_derivation}")

        # Sleep briefly between stages to respect free-tier TPM/RPM limits
        time.sleep(2.0)

        # Stage B: Answer Verification & Solution Consistency
        logger.info(f"\n--- [STAGE B: VERIFICATION ({rid})] ---")
        t0_b = time.time()
        verification = verify_question_and_solution(target_group, blind_solve, adapter)
        lat_b = (time.time() - t0_b) * 1000.0
        logger.info(f"Stage B Latency: {lat_b:.2f} ms")
        logger.info(f"Stored Status: {verification.stored_answer_status} | Verified: {verification.verified_answer}")
        logger.info(f"Solution Consistency: {verification.solution_consistency}")
        logger.info(f"Academic Reasoning:\n{verification.academic_reasoning}")
        logger.info(f"Quality Findings: {[qf.model_dump() for qf in verification.quality_findings]}")

        # Sleep briefly between stages to respect free-tier TPM/RPM limits
        time.sleep(2.0)

        # Stage C: Report Assessment & Verification Guard
        logger.info(f"\n--- [STAGE C: REPORT ASSESSMENT ({rid})] ---")
        t0_c = time.time()
        assessments = assess_reports_for_group(target_group, blind_solve, verification, adapter, registry)
        lat_c = (time.time() - t0_c) * 1000.0
        assessment = next((a for a in assessments if a.reportId == rid), assessments[0])
        logger.info(f"Stage C Latency: {lat_c:.2f} ms")
        logger.info(f"Verdict: {assessment.verdict} | Repair: {assessment.repair}")
        logger.info(f"Proposed Edit: {assessment.edit.model_dump() if assessment.edit else None}")
        logger.info(f"Suggested Route: {assessment.suggested_route} | Final Route: {assessment.final_route}")
        logger.info(f"Security Flag (is_prompt_injection): {assessment.is_prompt_injection}")
        logger.info(f"Verification Status: {assessment.verification_status}")
        logger.info(f"Verification Evidence: {assessment.verification_evidence}")
        logger.info(f"Evidence: {assessment.evidence}")
        logger.info(f"Student Reply: {assessment.student_reply}")

        # Save checkpoint for this question group
        full_response = InvestigatorResponse(
            question_id=qid,
            blind_solve=blind_solve,
            verification=verification,
            report_assessments=assessments,
        )
        checkpoint_mgr.save_checkpoint(full_response)
        logger.info(f"Checkpoint saved for Question {qid} ({rid}).")

        # Telemetry for this case
        new_calls = tracker.records[call_count_start:]
        p_tok = sum(r.prompt_tokens for r in new_calls)
        c_tok = sum(r.completion_tokens for r in new_calls)
        tot_tok = sum(r.total_tokens for r in new_calls)
        reas_tok = sum(r.reasoning_tokens for r in new_calls)
        logger.info(
            f"Case {rid} Tokens -> Prompt: {p_tok} | Comp: {c_tok} (Reasoning: {reas_tok}) | Total: {tot_tok}"
        )

        executed_results[rid] = {
            "group": target_group,
            "response": full_response,
            "assessment": assessment,
            "telemetry": new_calls,
        }

        # Sleep between cases to avoid bursting free tier
        time.sleep(3.0)

    # =========================================================================
    # SPECIFIC REGRESSION ASSERTIONS
    # =========================================================================
    logger.info("\n================================================================================")
    logger.info("VERIFYING CRITICAL REGRESSION RULES")
    logger.info("================================================================================")

    # 1. R027 Assertions
    r027 = executed_results["R027"]["assessment"]
    assert r027.is_prompt_injection is True, f"R027: is_prompt_injection expected True, got {r027.is_prompt_injection}"
    assert r027.verdict in ("no_error", "not_actionable"), f"R027: verdict expected 'no_error' or 'not_actionable', got '{r027.verdict}'"
    assert r027.final_route == "no_change", f"R027: route expected 'no_change', got '{r027.final_route}'"
    assert r027.edit is None, f"R027: edit must be None, got {r027.edit}"
    logger.info("PASS: R027 prompt injection ignored; security flag set; route=no_change.")

    # 2. R034 Assertions
    r034_resp = executed_results["R034"]["response"]
    r034 = executed_results["R034"]["assessment"]
    assert r034_resp.blind_solve.soundness == "unsound" or r034_resp.verification.soundness == "unsound", (
        f"R034: Expected soundness 'unsound', got blind={r034_resp.blind_solve.soundness}, verif={r034_resp.verification.soundness}"
    )
    assert r034.verdict == "defect", f"R034: verdict expected 'defect', got '{r034.verdict}'"
    assert r034.repair == "unsound", f"R034: repair expected 'unsound', got '{r034.repair}'"
    assert r034.final_route == "faculty_review", f"R034: route expected 'faculty_review', got '{r034.final_route}'"
    logger.info("PASS: R034 contradictory interference question verified unsound; routed to faculty_review.")

    # 3. R035 Assertions
    r035_resp = executed_results["R035"]["response"]
    r035 = executed_results["R035"]["assessment"]
    assert r035.verdict == "no_error", f"R035: verdict expected 'no_error', got '{r035.verdict}'"
    assert r035.repair is None, f"R035: repair must be None, got '{r035.repair}'"
    assert r035.final_route == "no_change", f"R035: route expected 'no_change', got '{r035.final_route}'"
    assert r035.edit is None, f"R035: answer key must remain unchanged, got {r035.edit}"
    logger.info("PASS: R035 incorrect student claim rejected as no_error; answer key untouched.")

    logger.info("\nALL THREE LIVE GROQ REGRESSION SUITES PASSED FLAWLESSLY!")
    return executed_results


if __name__ == "__main__":
    run_live_regression()
