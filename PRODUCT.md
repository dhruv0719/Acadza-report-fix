# Acadza Product Philosophy: AI Report → Fix Loop

---

### 1. Who Loses the Most When a Question is Broken?
The biggest loser is **the serious, borderline rank-seeking student (95th–98th percentile)** aiming for top IIT/AIIMS seats. 
- **The Psychological Damage:** When a mathematically sound student calculates $P = 4800\text{ N/m}^2$ (Option D) but the platform insists the answer is $4556$ (Option A), they spend 20 minutes re-deriving the problem, questioning their fundamentals, and eroding trust in the test series. During timed full-length mocks, this creates cognitive panic and severe time starvation.
- **The Scoring Penalty:** In JEE Advanced, an incorrect key inflicts a 5-mark swing ($-1$ negative marking instead of $+4$). In a competitive exam where 5 marks separate 1,500 ranks, a platform defect directly jeopardizes a student's career trajectory.
- **How Our Architecture Reflects This:**
  1. **Strict Isolated Blind Solving (Stage A):** The AI solves problems from pure first principles without seeing stored keys or student comments, eliminating confirmation bias.
  2. **Truthful, Empathetic Communication:** Students never receive dismissive "thank you for your feedback" templates. When their derivation is correct, the reply specifically validates their calculation and explains the staged correction state.

---

### 2. What We Would NEVER Let the AI Auto-Apply
1. **Question Stem Rewrites or Numerical Constant Alterations:** The AI is strictly barred from modifying physics constants, problem parameters, or boundary conditions. If an author omitted an inductance value $L$ (as in AC circuit question `60f742f6...`), the engine routes directly to **Faculty Review**. Fabricating an unstated parameter alters the academic integrity of the item.
2. **Question Deletions / Deprecations:** Deleting a question alters the total maximum marks of past tests and distorts historical percentile cutoffs across cohorts.
3. **Unsound Questions with Contradictory Logic:** In assertion-reason or multi-correct items where both statements are false and no valid option exists (e.g., R034), the AI must fail closed to **Faculty Review**. Automatic guessing would commit a flawed option to production.

---

### 3. The One Metric We Would Watch in Week 1
**Faculty Override Rate on Staged Auto-Applies ($\text{FOR}$):**
$$\text{FOR} = \frac{\text{Staged Auto-Applies Rejected or Modified by Faculty}}{\text{Total Staged Auto-Applies}} \times 100$$
- **Target:** **$< 1.5\%$**.
- **Why:** Auto-apply only triggers when Stage A derivation, Stage B academic consistency, and deterministic calculations achieve full convergence. If faculty must override a staged fix, it signals an algorithmic false positive or parser failure. Monitoring $\text{FOR}$ hourly during Week 1 safeguards against database pollution and guarantees safety.

---

### 4. One Idea Beyond This Brief We Pitch to Acadza
**"Retroactive Rank Impact Simulator & Automated Score Restoration"**
When an answer key defect is approved (e.g., flipping R004 from Key A to Key D):
- Instead of silently updating the database, the engine runs an asynchronous counterfactual calculation across all students who attempted that question in past mocks.
- It computes the $+5$ mark swing, calculates the revised percentile and simulated All India Rank (AIR), and pushes an in-app proactive notification:
  > *"We caught an answer key error on Question #68e870ef that you answered correctly. Your score has been adjusted by +5 marks, moving your mock rank from AIR 3,420 to AIR 2,890. Keep pushing!"*
- **Product Impact:** Transforms a potential customer churn event (a broken question) into an authentic high-trust brand differentiator that proves Acadza cares obsessively about exam accuracy.

