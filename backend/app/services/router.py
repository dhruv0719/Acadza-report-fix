import logging
from typing import List, Tuple

from app.models.investigation import InternalReportAssessment, RouteType, VerificationStatus
from app.models.question import NormalizedQuestion
from app.models.taxonomy import TaxonomyRegistry

logger = logging.getLogger(__name__)

# Minimum confidence required for automatic application of repairs
AUTO_APPLY_CONFIDENCE_THRESHOLD = 0.85


def calculate_final_route(
    assessment: InternalReportAssessment,
    question: NormalizedQuestion,
    registry: TaxonomyRegistry,
) -> Tuple[RouteType, List[str]]:
    """Calculates the authoritative final route using deterministic Python validation.
    
    CRITICAL:
    - The LLM's suggested_route is advisory only.
    - Verification and validation fail closed.
    - Any unsafe, unverified, out-of-scope, or ambiguous proposed repair defaults to 'faculty_review'.
    - Non-defects must route strictly to 'no_change'.
    """
    errors: List[str] = []

    # 1. Non-defect verdicts must always route to 'no_change'
    if assessment.verdict != "defect":
        if assessment.repair is not None:
            errors.append(f"Non-defect verdict '{assessment.verdict}' cannot have repair '{assessment.repair}'. Clearing repair.")
            assessment.repair = None
        if assessment.edit is not None:
            errors.append(f"Non-defect verdict '{assessment.verdict}' cannot have proposed edit. Clearing edit.")
            assessment.edit = None
        return "no_change", errors

    # 2. Defect verdicts MUST have a valid repair from the closed taxonomy
    if not assessment.repair or not registry.is_valid_repair(assessment.repair):
        errors.append(f"Invalid or missing repair key: '{assessment.repair}'. Routing to faculty_review.")
        return "faculty_review", errors

    # 3. Check official taxonomy auto-apply permission
    if not registry.is_auto_repair(assessment.repair):
        # Human review mandatory for repairs like identical_options, diagram, wrong_question, unsound, wrong_chapter, syllabus
        return "faculty_review", errors

    # 4. Check that proposed edit is present for auto-applicable defects
    if assessment.edit is None:
        errors.append(f"Repair '{assessment.repair}' is auto-applicable but no surgical edit was provided.")
        return "faculty_review", errors

    # 5. Check allowed fields scope from taxonomy.json
    allowed_fields = registry.get_repair_fields(assessment.repair)
    if assessment.edit.field not in allowed_fields:
        errors.append(f"Proposed edit field '{assessment.edit.field}' is outside allowed fields {allowed_fields} for repair '{assessment.repair}'.")
        return "faculty_review", errors

    # 6. Verify textual find/replace occurs EXACTLY once
    if assessment.edit.field in ("question", "solution") and assessment.edit.find:
        target_text = question.raw_question_html if assessment.edit.field == "question" else question.raw_solution_html
        occurrences = target_text.count(assessment.edit.find)
        if occurrences != 1:
            errors.append(f"Target substring '{assessment.edit.find}' occurs {occurrences} times in {assessment.edit.field} (must occur exactly once for deterministic patch).")
            return "faculty_review", errors

    # 7. High-stakes verification guard for answer changes
    if assessment.edit.field == "answer" or assessment.repair == "answer_key":
        if assessment.verification_status != "passed":
            errors.append(f"Answer key change requires verification_status 'passed', but got '{assessment.verification_status}'.")
            return "faculty_review", errors

        # Validate answer value shape
        val = assessment.edit.replace
        if question.question_type == "scq":
            if not isinstance(val, str) or val.strip().upper() not in ("A", "B", "C", "D"):
                errors.append(f"Invalid SCQ replacement answer '{val}'. Must be single key A, B, C, or D.")
                return "faculty_review", errors
        elif question.question_type == "mcq":
            if not isinstance(val, list) or not all(isinstance(x, str) and x.strip().upper() in ("A", "B", "C", "D") for x in val):
                errors.append(f"Invalid MCQ replacement answer '{val}'. Must be list of valid keys.")
                return "faculty_review", errors
        elif question.question_type == "integerQuestion":
            val_str = str(val).strip()
            if not val_str.lstrip("-").isdigit():
                errors.append(f"Invalid integer replacement answer '{val}'. Must be integer.")
                return "faculty_review", errors

    # 8. Never auto-apply invented options
    if assessment.repair == "option_repair":
        # If question is missing an option entirely (e.g. only A, B, C), never auto-apply unless proven
        keys = [o.key for o in question.options]
        if len(keys) < 4:
            # Missing option cannot be invented
            errors.append(f"Question has missing options ({keys}). Missing option text must be verified by faculty, not invented.")
            return "faculty_review", errors

    # 9. Confidence threshold
    if assessment.confidence < AUTO_APPLY_CONFIDENCE_THRESHOLD:
        errors.append(f"Confidence {assessment.confidence:.2f} is below threshold {AUTO_APPLY_CONFIDENCE_THRESHOLD:.2f}.")
        return "faculty_review", errors

    # 10. Prompt injection safety
    if assessment.is_prompt_injection:
        errors.append("Report flagged as prompt injection; automatic edits prohibited.")
        return "faculty_review", errors

    return "auto_apply", errors

