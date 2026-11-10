import logging
from typing import Optional, Tuple

from app.models.investigation import (
    BlindSolveOutput,
    ProposedEdit,
    QuestionVerificationOutput,
    VerificationStatus,
)
from app.models.question import NormalizedQuestion

logger = logging.getLogger(__name__)


class HighStakesVerifier:
    """Secondary verification engine for high-risk triage actions.
    
    CRITICAL:
    - Fails closed: anything missing, ambiguous, or contradictory results in 'failed' or 'inconclusive'.
    - Confidence alone never authorizes an answer key change.
    - Requires independent proof from BlindSolve and domain consistency.
    """

    @staticmethod
    def verify(
        question: NormalizedQuestion,
        proposed_repair: Optional[str],
        proposed_edit: Optional[ProposedEdit],
        blind_solve: BlindSolveOutput,
        verification: QuestionVerificationOutput,
    ) -> Tuple[VerificationStatus, str]:
        """Executes secondary verification on high-risk operations."""
        # 1. Check if operation is high-risk
        is_answer_change = proposed_repair == "answer_key" or (proposed_edit and proposed_edit.field == "answer")
        is_unsound = proposed_repair == "unsound"
        is_wrong_question = proposed_repair == "wrong_question"
        is_solution_replacement = proposed_repair in ("solution_fix", "solution_missing") and proposed_edit and proposed_edit.field == "solution"

        if not (is_answer_change or is_unsound or is_wrong_question or is_solution_replacement):
            return "not_required", "Operation does not involve high-stakes answer replacement or soundness mutation."

        # 2. Answer key modification verification
        if is_answer_change:
            if proposed_edit is None or proposed_edit.replace is None:
                return "failed", "Verification failed: Proposed answer key edit lacks replacement value."

            target_val = proposed_edit.replace
            # Check 1: Did blind solve yield a sound problem?
            if blind_solve.soundness != "sound":
                return "inconclusive", f"Blind solve flagged problem soundness as '{blind_solve.soundness}', cannot verify key change."

            # Check 2: Does blind solve answer match the proposed replacement?
            derived = blind_solve.derived_answer
            if derived is None:
                return "inconclusive", "Blind solve could not independently derive a conclusive answer."

            # Standardize comparison
            def _normalize(val):
                if isinstance(val, list):
                    return sorted([str(x).strip().upper() for x in val])
                return str(val).strip().upper()

            if _normalize(derived) != _normalize(target_val):
                return "failed", f"Disagreement: Blind solve derived '{derived}', but proposed edit replaces answer with '{target_val}'."

            # Check 3: Is there verified academic reasoning?
            if not blind_solve.step_by_step_derivation or len(blind_solve.step_by_step_derivation.strip()) < 20:
                return "inconclusive", "Insufficient mathematical derivation in blind solve to justify automatic key alteration."

            return "passed", f"Verified: Independent derivation ({derived}) matches proposed answer replacement with sound proof."

        # 3. Unsound question verification
        if is_unsound:
            if verification.soundness != "unsound":
                return "failed", f"Unsound classification rejected: Verification marked soundness as '{verification.soundness}'."
            return "passed", "Verified: Inherent academic contradiction or physical invalidity confirmed in question/solution structure."

        # 4. Wrong question verification
        if is_wrong_question:
            if verification.solution_consistency != "unrelated":
                return "inconclusive", f"Solution consistency is '{verification.solution_consistency}', not confirmed as completely unrelated question."
            return "passed", "Verified: Solution is conclusively from an entirely different question."

        # 5. Solution fix verification
        if is_solution_replacement:
            if verification.solution_consistency == "consistent":
                return "failed", "Solution was verified as consistent with question; replacement not justified."
            return "passed", f"Verified: Stored solution had flaw ({verification.solution_consistency}); surgical correction approved."

        return "inconclusive", "Verification ended with indeterminate criteria."

