# Acadza AI Report → Fix Loop System

> Production-grade automated defect triage, scientific verification, and faculty review console for Acadza's JEE/NEET Question Bank.

[![Backend Tests](https://img.shields.io/badge/pytest-60%20passed-emerald)](file:///d:/acadza-report-fix/backend/tests)
[![Next.js Build](https://img.shields.io/badge/Next.js%2014-Compiled%20Clean-blue)](file:///d:/acadza-report-fix/frontend)
[![Primary Model](https://img.shields.io/badge/Groq%20LLM-openai%2Fgpt--oss--120b-purple)](file:///d:/acadza-report-fix/LLM_USAGE.md)
[![License](https://img.shields.io/badge/License-Proprietary-slate)](file:///d:/acadza-report-fix)

---

## 1. System Overview

Acadza serves over 8 lakh JEE/NEET questions to students preparing for competitive national examinations. When students tap **"Report error"**, their submissions range from valid answer-key discrepancies and missing diagrams to false conceptual claims, app confusion, and adversarial prompt injections.

This system sits between student error reports and production question updates. It automates triage by combining **DOM-based MathML parsing**, **deterministic rule prechecks**, **isolated three-stage AI investigation**, **closed-form calculation proofs**, and an **interactive Faculty Review Console**.

```
Student Reports (44) ───► Deterministic Precheck ───► Question-Level Grouping (39)
                                                            │
┌─────────────────────────── Three-Stage AI Engine ─────────┴────────────────────────┐
│                                                                                    │
│   Stage A: BlindSolve               Stage B: Verification        Stage C: Triage   │
│   ┌────────────────────────┐        ┌──────────────────────┐     ┌───────────────┐ │
│   │ Solves from pure first │───────►│ Compares with stored │────►│ Evaluates     │ │
│   │ principles without     │        │ key, solution text,  │     │ report, sets  │ │
│   │ key or student comment │        │ & math engine proofs │     │ verdict/edit  │ │
│   └────────────────────────┘        └──────────────────────┘     └───────────────┘ │
└────────────────────────────────────────────┬───────────────────────────────────────┘
                                             ▼
                               Fail-Closed Python Router
                                             │
             ┌───────────────────────────────┼──────────────────────────────┐
             ▼                               ▼                              ▼
      auto_apply (17)               faculty_review (10)               no_change (17)
  (Passed all math checks)       (Unsound / Missing Data)        (False Claims / Spams)
```

---

## 2. Key Architecture Pillars

### A. Non-Destructive MathML DOM Normalizer (`backend/app/services/normalizer.py`)
- Standardizes messy production HTML containing inline MathML (`<math>`, `<mrow>`, `<mo>`), nested formatting spans, and multi-line options without discarding original markup.
- Extracts stem text, parses options into structured key-value pairs, and identifies question types (`scq`, `mcq`, `integerQuestion`).
- Never mutates the raw canonical source files in `data/raw/`.

### B. Deterministic Pre-Check Engine (`backend/app/services/precheck.py`)
- Executes instant, zero-cost programmatic checks prior to LLM invocation:
  - Missing or blank option markers.
  - Duplicate option text across keys.
  - Figure references ("as shown in figure") lacking image attachments (e.g. question `622df25ab70e4b50e44ff837`).
  - Unit omissions and target answer anomalies.

### C. Isolated Three-Stage AI Investigation (`backend/app/services/investigator.py`)
1. **Stage A (BlindSolve):** Solves the question in total isolation. Stored answer keys, worked solutions, and student comments are strictly withheld to eliminate confirmation bias and render prompt injection attacks impossible.
2. **Stage B (Answer Verification & Mathematical Proof):** An academic consistency check comparing the derived answer with the stored key. Augmented by `DeterministicCalculationEngine` (`verifier.py`) for closed-form physical verification (e.g. kinetic theory pressure $P = \frac{1}{3}\rho v_{\text{rms}}^2 = 4800\text{ N/m}^2$).
3. **Stage C (Report Assessment):** Evaluates the student's specific comment against the verified ground truth. Selects verdicts (7) and repairs (18) strictly from the closed `taxonomy.json`.

### D. Fail-Closed Python Router Guard (`backend/app/services/router.py`)
- The LLM's routing suggestion is strictly advisory. Final routing is governed by deterministic Python logic:
  - Only repairs marked `auto: true` in `taxonomy.json` may be staged for automatic application.
  - The proposed edit must touch fields authorized for that repair type.
  - Answer-key edits require an explicit old-value verification check (`field="answer"`, `find="A"`, `replace="D"`).
  - Any uncertainty, missing option text, or unverified derivation fails closed to `faculty_review`.

### E. Persistent Review Storage (`backend/app/services/review_storage.py`)
- Records all faculty actions (`approve`, `reject`, `modify`) in an ACID-compliant SQLite database (`data/faculty_reviews.db`) with full JSON synchronization (`data/faculty_reviews.json`).
- Stores reviewer name, timestamp, reviewer notes, previous value, staged new value, and audit trail history across restarts.

---

## 3. Local Setup & Running Instructions

### Prerequisites
- Python 3.9+ installed
- Node.js 18+ and npm installed

### Backend Setup
1. Open PowerShell or Terminal and navigate to the project root:
   ```powershell
   cd d:\acadza-report-fix
   ```
2. Install Python dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Configure environment variables:
   ```powershell
   cp .env.example .env
   # Add your GROQ_API_KEY if running live investigations
   ```
4. Start the FastAPI backend:
   ```powershell
   $env:PYTHONPATH="backend"
   py -3.9 -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```
   - API Health: `http://127.0.0.1:8000/api/health`
   - Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### Frontend Setup
1. In a separate terminal, navigate to the frontend directory:
   ```powershell
   cd frontend
   npm install
   ```
2. Launch the Next.js development server:
   ```powershell
   npm run dev
   ```
   - Faculty Console: `http://localhost:3000`

### Running the Test Suite
Run all 60 unit, integrity, regression, and API endpoint tests:
```powershell
py -3.9 -m pytest backend/tests -v
```

---

## 4. Faculty Review Console Walkthrough

The Next.js/TypeScript console provides five integrated views designed for high-throughput academic review:

1. **Triage Queue (44 Reports):**
   - Search across report IDs, question IDs, comments, and topics.
   - Filter by Route (`Auto Apply`, `Faculty Review`, `No Change`), Subject, and Verdict.
   - Column sorting on Report ID, Confidence, and Route.
   - Faculty approval badges: `PENDING`, `APPROVED (STAGED)`, `REJECTED`, `MODIFIED (STAGED)`.

2. **Split-Pane Inspection Modal:**
   - **Left Pane:** Question stem with native MathML Core typography, option cards with derived answer highlighting, worked solution, and missing figure warnings.
   - **Right Pane:** Student comment details, three-stage AI investigation trace, mathematical proof badge, surgical mutation visual diff (`find` &rarr; `replace`), truthful student reply preview, and faculty action buttons (`Approve`, `Reject`, `+ Customize Patch`).

3. **Live Groq Verification (4 Cases):**
   - Detailed spotlight on the four live-executed regression cases (R004, R027, R034, R035) with token consumption and latency metrics.

4. **Intrinsic Corpus Defects (14 Defects):**
   - Complete catalog of 14 content errors discovered across the 43-question corpus (missing parameters, contradictory solution steps, missing option keys) isolated independently of student reports.

5. **Unreported Questions Audit (4 Questions):**
   - First-principles mathematical derivations proving the soundness of the four questions that received zero student defect reports.

6. **LLM Telemetry:**
   - Complete token ledger logging prompt tokens, completion tokens, reasoning tokens, latency, and status codes for authentic Groq API calls.

---

## 5. Deployment Guide

### Frontend Deployment (Vercel)
1. Push repository to GitHub.
2. In the Vercel Dashboard, select **Add New Project** and import the repository.
3. Configure project settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Next.js`
4. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL`: URL of your hosted backend (e.g. `https://acadza-triage-backend.onrender.com/api`).
5. Click **Deploy**.

### Backend Deployment (Render / Docker)
A production `Dockerfile` and `render.yaml` are included at the root:
1. On Render.com, create a **New Web Service** connected to your repository.
2. Select **Docker** or **Python** runtime.
3. Set Environment Variables:
   - `PYTHONPATH`: `backend`
   - `ENVIRONMENT`: `production`
   - `GROQ_API_KEY`: Your Groq API key (optional for browsing precomputed results).
4. The service will build dependencies and start:
   `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`

---

## 6. Honest Limitations & Provenance Disclosure

- **Authentic Live Execution vs Precomputed Baselines:** Exactly **4 critical regression cases** (R004, R027, R034, R035) totaling 12 API calls and 36,704 tokens were executed live on Groq using `openai/gpt-oss-120b`. The remaining 35 question groups utilize deterministic precomputed baselines to prevent exhausting free-tier rate limits (Groq RPM/TPM constraints). No claim of 44 simultaneous live LLM calls is made.
- **MathML Token Spacing:** Spacing inside MathML XML tokens (e.g. `k g`, `v_ r m s`) represents standard XML tokenization. Browsers render these natively as $\text{kg/m}^3$ without spacing defects. The system enforces a strict negative prompt constraint to prevent false-positive spacing complaints.
- **Fail-Closed Human Escalation:** The AI cannot fabricate omitted question parameters or repair contradictory options where no valid choice exists (such as R034). In all such cases, the system fails closed to `faculty_review`.
- **Surgical Staging vs Production Database Commit:** Approved patches are labeled `approved_staged` in the audit database. They are prepared for staging and batch synchronization, preserving raw source files in `data/raw/` in an unmutated state.

---

## 7. Submission Results Schema (`results.json`)

The final submission file [`results.json`](file:///d:/acadza-report-fix/results.json) contains exactly **44 records**, each formatted with the required nine fields:

```json
{
  "reportId": "R004",
  "questionId": "68e870ef42c06737d6e565c4",
  "verdict": "defect",
  "repair": "answer_key",
  "edit": {
    "field": "answer",
    "find": "A",
    "replace": "D"
  },
  "route": "auto_apply",
  "confidence": 0.98,
  "evidence": "Kinetic theory pressure formula P = (1/3)*rho*(v_rms)^2 with rho=4 kg/m^3 and v_rms=60 m/s yields P = (1/3)*4*3600 = 4800 N/m^2 (Option D). Stored answer is Option A (4556), which is physically incorrect. Student suggested 8225 (Option B), which is mathematically false.",
  "student_reply": "Thank you for flagging this question. We independently solved the problem from first principles and verified that the correct pressure is 4800 N/m² (Option D). A correction has been staged to update the answer key from Option A to Option D."
}
```

---

## 8. Repository Structure

```
acadza-report-fix/
├── .env.example                       # Documented environment variables template
├── .gitignore                          # Protected secrets, DBs, and virtualenvs
├── Dockerfile                         # Container specification for backend deployment
├── LLM_USAGE.md                       # Authentic Groq token telemetry & call ledger
├── PRODUCT.md                         # 1-page product philosophy & strategy memo
├── PROMPTS.md                         # Full prompt evolutions, AI prompts & failures log
├── README.md                          # Complete system guide & setup instructions
├── render.yaml                        # Infrastructure-as-code for Render backend
├── results.json                       # Canonical 44-record submission artifact
├── backend/
│   ├── requirements.txt               # Backend dependencies
│   ├── app/
│   │   ├── main.py                    # FastAPI application & CORS configuration
│   │   ├── api/routes.py              # 10 API endpoints for console & reviews
│   │   ├── core/config.py             # Project-relative path settings
│   │   ├── models/                    # Pydantic schemas (question, report, result)
│   │   └── services/                  # Normalizer, Precheck, Investigator, Router
│   └── tests/                         # 60 automated test cases (100% green)
├── data/
│   ├── raw/                           # Untouched raw source datasets (questions, reports)
│   ├── faculty_reviews.db             # Persistent SQLite audit database
│   ├── faculty_reviews.json           # Synchronized JSON faculty review ledger
│   ├── investigation_checkpoints.json # Checkpointed multi-stage investigation traces
│   ├── llm_usage_log.json             # Raw API call logs with token telemetry
│   ├── question_quality_findings.json # 14 intrinsic corpus content defects
│   ├── results.json                   # Verified results mirror
│   └── unreported_question_audit.json # Scientific proofs for 4 unreported questions
└── frontend/
    ├── package.json                   # Next.js 14, Tailwind, Lucide dependencies
    ├── vercel.json                    # Vercel deployment preset
    └── src/
        ├── app/                       # Next.js App Router (page.tsx, layout.tsx)
        ├── components/                # TriageTable, Modal, LiveGroq, Telemetry, etc.
        ├── lib/api.ts                 # Typed API client functions
        └── types/index.ts             # TypeScript domain definitions
```
