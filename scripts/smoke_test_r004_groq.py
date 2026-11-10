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
    investigate_question_group,
    verify_question_and_solution,
)
from app.services.llm_adapter import LLMAdapter, LLMConfig
from app.services.usage_tracker import UsageTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoke_test_r004")


def run_smoke_test():
    logger.info("================================================================================")
    logger.info("STARTING LIVE GROQ API SMOKE TEST: Question 68e870ef42c06737d6e565c4 (R004)")
    logger.info("================================================================================")

    # 1. Verify credentials and configuration
    config = LLMConfig(provider="groq")
    if not config.groq_api_key:
        logger.error("GROQ_API_KEY not found in .env. Cannot perform live smoke test.")
        sys.exit(1)

    logger.info(f"Target LLM Provider : {config.provider}")
    logger.info(f"Primary Model ID    : {config.model}")
    logger.info(f"Fallback Model ID   : {config.fallback_model}")
    logger.info(f"Temperature         : {config.temperature}")
    logger.info(f"Reasoning Effort    : {config.reasoning_effort}")
    logger.info(f"Structured Output   : {config.structured_output}")
    logger.info("GROQ_API_KEY is present and securely loaded.")

    # 2. Find group for R004
    groups = group_reports_by_question()
    target_group = next((g for g in groups if g.question_id == "68e870ef42c06737d6e565c4"), None)
    if not target_group:
        logger.error("Target question group 68e870ef42c06737d6e565c4 not found in grouped reports.")
        sys.exit(1)

    q = target_group.normalized_question
    report = target_group.reports[0]
    logger.info(f"Question ID: {q.id}")
    logger.info(f"Question Type: {q.question_type}")
    logger.info(f"Subject: {q.subject} | Chapter: {q.chapter}")
    logger.info(f"Stored Answer: {q.raw_answer}")
    logger.info(f"Student Report ID: {report.reportId}")
    logger.info(f"Student Comment: '{report.comment}'")

    adapter = LLMAdapter(config=config)
    registry = TaxonomyRegistry.get_default()
    tracker = UsageTracker.get_instance()
    initial_call_count = len(tracker.records)

    # 3. Stage A: Truly Isolated Blind Solve
    logger.info("\n--- [STAGE A: TRULY ISOLATED BLIND SOLVE] ---")
    t0_stage_a = time.time()
    blind_solve = blind_solve_question(target_group, adapter)
    time_stage_a = (time.time() - t0_stage_a) * 1000.0

    logger.info(f"Stage A Latency     : {time_stage_a:.2f} ms")
    logger.info(f"Soundness Status    : {blind_solve.soundness}")
    logger.info(f"Derived Answer      : {blind_solve.derived_answer}")
    logger.info(f"Confidence Score    : {blind_solve.confidence}")
    logger.info(f"Derivation Steps    :\n{blind_solve.step_by_step_derivation}")

    # 4. Stage B: Answer Verification & Solution Consistency
    logger.info("\n--- [STAGE B: ANSWER & SOLUTION VERIFICATION] ---")
    t0_stage_b = time.time()
    verification = verify_question_and_solution(target_group, blind_solve, adapter)
    time_stage_b = (time.time() - t0_stage_b) * 1000.0

    logger.info(f"Stage B Latency     : {time_stage_b:.2f} ms")
    logger.info(f"Stored Answer Status: {verification.stored_answer_status}")
    logger.info(f"Verified Answer     : {verification.verified_answer}")
    logger.info(f"Solution Consistency: {verification.solution_consistency}")
    logger.info(f"Academic Reasoning  :\n{verification.academic_reasoning}")
    logger.info(f"Quality Findings    : {[qf.model_dump() for qf in verification.quality_findings]}")

    # 5. Stage C: Report Assessment & Verification Guard
    logger.info("\n--- [STAGE C: REPORT ASSESSMENT & VERIFICATION GUARD] ---")
    t0_stage_c = time.time()
    assessments = assess_reports_for_group(target_group, blind_solve, verification, adapter, registry)
    time_stage_c = (time.time() - t0_stage_c) * 1000.0

    assessment = assessments[0]
    logger.info(f"Stage C Latency     : {time_stage_c:.2f} ms")
    logger.info(f"Official Verdict    : {assessment.verdict}")
    logger.info(f"Official Repair     : {assessment.repair}")
    logger.info(f"Proposed Edit       : {assessment.edit.model_dump() if assessment.edit else None}")
    logger.info(f"Suggested Route     : {assessment.suggested_route}")
    logger.info(f"Final Route (Python): {assessment.final_route}")
    logger.info(f"Verification Status : {assessment.verification_status}")
    logger.info(f"Verification Notes  : {assessment.verification_evidence}")
    logger.info(f"Evidence Summary    : {assessment.evidence}")
    logger.info(f"Student Reply       : {assessment.student_reply}")

    # 6. Save Persistent Checkpoint
    checkpoint_mgr = CheckpointManager()
    from app.models.investigation import InvestigatorResponse
    full_response = InvestigatorResponse(
        question_id=target_group.question_id,
        blind_solve=blind_solve,
        verification=verification,
        report_assessments=assessments,
    )
    checkpoint_mgr.save_checkpoint(full_response)
    logger.info("Persistent checkpoint saved successfully.")

    # 7. Collect Telemetry and Token Usage
    logger.info("\n================================================================================")
    logger.info("LIVE GROQ API USAGE TELEMETRY & TOKEN CONSUMPTION")
    logger.info("================================================================================")

    new_records = tracker.records[initial_call_count:]
    total_prompt_tok = sum(r.prompt_tokens for r in new_records)
    total_comp_tok = sum(r.completion_tokens for r in new_records)
    total_tok = sum(r.total_tokens for r in new_records)
    total_reasoning_tok = sum(r.reasoning_tokens for r in new_records)

    for idx, r in enumerate(new_records, 1):
        logger.info(
            f"Call #{idx} [{r.call_type}] -> Model: {r.model} | Mode: {r.structured_output_mode} | "
            f"Prompt Tok: {r.prompt_tokens} | Comp Tok: {r.completion_tokens} (Reasoning: {r.reasoning_tokens}) | "
            f"Total Tok: {r.total_tokens} | Latency: {r.latency_ms:.2f} ms | Request ID: {r.request_id}"
        )

    logger.info("--------------------------------------------------------------------------------")
    logger.info(f"Total API Calls Made     : {len(new_records)}")
    logger.info(f"Total Prompt Tokens      : {total_prompt_tok}")
    logger.info(f"Total Completion Tokens  : {total_comp_tok}")
    logger.info(f"Total Tokens Consumed    : {total_tok}")
    logger.info(f"Total Reasoning Tokens   : {total_reasoning_tok}")
    logger.info(f"Total Wall Clock Latency : {(time_stage_a + time_stage_b + time_stage_c):.2f} ms")
    logger.info("================================================================================")

    # 8. Assert Academic and Functional Correctness
    assert blind_solve.derived_answer in ("D", "4800", "4800 N / m^2"), f"Expected derived answer 'D', got {blind_solve.derived_answer}"
    assert verification.stored_answer_status == "incorrect", f"Expected stored answer to be marked incorrect, got {verification.stored_answer_status}"
    assert assessment.verdict == "defect", f"Expected verdict 'defect', got {assessment.verdict}"
    assert assessment.repair == "answer_key", f"Expected repair 'answer_key', got {assessment.repair}"
    assert assessment.edit is not None and assessment.edit.field == "answer", "Expected edit on 'answer' field"
    assert assessment.final_route == "auto_apply", f"Expected route 'auto_apply', got {assessment.final_route}"
    assert "8225" not in str(assessment.edit.replace), f"Student's erroneous answer 8225 was improperly accepted in edit: {assessment.edit}"

    logger.info("\nALL ACADEMIC GROUND TRUTH ASSERTIONS PASSED FOR R004!")
    return full_response


if __name__ == "__main__":
    run_smoke_test()

