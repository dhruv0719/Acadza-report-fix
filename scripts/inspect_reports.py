import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.data_loader import load_normalized_questions, load_raw_reports
from app.services.precheck import run_all_prechecks_for_question

reps = load_raw_reports()
qs = {q.id: q for q in load_normalized_questions()}

for r in sorted(reps, key=lambda x: x['reportId']):
    q = qs[r['questionId']]
    findings = run_all_prechecks_for_question(q)
    f_str = ", ".join([f.check_id for f in findings]) if findings else "None"
    print(f"[{r['reportId']}] Question: {q.id} ({q.question_type}) - Subject: {q.subject}, Chapter: {q.chapter}")
    print(f"   Student comment: {repr(r['comment'])} (Source: {r['source']})")
    print(f"   Precheck Findings: {f_str}")
    print(f"   Stem: {q.stem_text[:110]}")
    if q.options:
        opts = " // ".join([f"({o.key}) {o.text[:30]}" for o in q.options])
        print(f"   Options: {opts}")
    print(f"   Raw answer: {repr(q.raw_answer)} | Norm answer: {repr(q.normalized_answer)}")
    print(f"   Solution preview: {q.solution_text[:120]}")
    print("-" * 80)

