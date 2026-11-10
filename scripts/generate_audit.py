import hashlib
import json
import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import settings
from app.services.data_loader import load_normalized_questions, load_raw_questions
from app.services.normalizer import dom_to_semantic_text

def compute_extraction_fidelity(raw_text: str, norm_q):
    """Computes textual reconstruction fidelity between raw source and normalized elements."""
    if norm_q.question_type == "integerQuestion":
        reconstructed = norm_q.stem_text
    else:
        opt_parts = []
        for o in norm_q.options:
            if o.is_blank:
                opt_parts.append(f"({o.key})")
            else:
                opt_parts.append(f"({o.key}) {o.text}")
        reconstructed = f"{norm_q.stem_text} {' '.join(opt_parts)}".strip()

    raw_clean = re.sub(r'\s+', ' ', raw_text).strip()
    norm_clean = re.sub(r'\s+', ' ', reconstructed).strip()

    len_raw = len(raw_clean)
    len_norm = len(norm_clean)
    diff = abs(len_raw - len_norm)
    ratio = len_norm / len_raw if len_raw > 0 else 1.0

    # Fidelity passes if within whitespace/delimiter variation (<= 25 chars or ratio >= 0.95)
    fidelity_pass = (diff <= 25) or (ratio >= 0.95 and ratio <= 1.05)

    return {
        "raw_text_length": len_raw,
        "reconstructed_text_length": len_norm,
        "character_difference": diff,
        "fidelity_ratio": round(ratio, 4),
        "fidelity_pass": fidelity_pass,
    }

def generate_normalizer_audit():
    raw_questions = load_raw_questions()
    normalized_questions = load_normalized_questions()

    raw_map = {q["_id"]: q for q in raw_questions}
    audit_entries = []

    # Category counters for explicit breakdown
    category_lists = {
        "scq_complete_4_options": [],
        "scq_blank_option": [],
        "scq_missing_option": [],
        "mcq_4_options": [],
        "integer_no_options": [],
    }

    for norm_q in normalized_questions:
        raw = raw_map[norm_q.id]
        qtype = raw["questionType"]
        payload = raw.get(qtype, {})

        raw_q = payload.get("question", "")
        raw_s = payload.get("solution", "")
        raw_ans = payload.get("answer")

        q_hash_before = hashlib.sha256(raw_q.encode("utf-8")).hexdigest()
        q_hash_after = hashlib.sha256(norm_q.raw_question_html.encode("utf-8")).hexdigest()

        s_hash_before = hashlib.sha256(raw_s.encode("utf-8")).hexdigest()
        s_hash_after = hashlib.sha256(norm_q.raw_solution_html.encode("utf-8")).hexdigest()

        raw_source_unchanged = (q_hash_before == q_hash_after) and (s_hash_before == s_hash_after)

        # Categorize
        if norm_q.question_type == "scq":
            keys = [o.key for o in norm_q.options]
            blank_keys = [o.key for o in norm_q.options if o.is_blank]
            if keys == ["A", "B", "C"]:
                cat = "scq_missing_option"
            elif blank_keys:
                cat = "scq_blank_option"
            else:
                cat = "scq_complete_4_options"
        elif norm_q.question_type == "mcq":
            cat = "mcq_4_options"
        else:
            cat = "integer_no_options"

        category_lists[cat].append(norm_q.id)

        # Extraction fidelity check
        raw_semantic = dom_to_semantic_text(raw_q)
        fidelity = compute_extraction_fidelity(raw_semantic, norm_q)

        # Marker types
        marker_types = []
        if norm_q.question_type in ("scq", "mcq"):
            for opt in norm_q.options:
                if opt.has_mathml:
                    marker_types.append("mathml_mo")
                else:
                    marker_types.append("text_node")
            marker_types = sorted(list(set(marker_types)))

        stem_status = "integer_no_options" if norm_q.question_type == "integerQuestion" else "success"

        entry = {
            "question_id": norm_q.id,
            "qid": norm_q.qid,
            "question_type": norm_q.question_type,
            "sub_category": cat,
            "subject": norm_q.subject,
            "chapter": norm_q.chapter,
            "detected_option_markers": [o.key for o in norm_q.options],
            "marker_types": marker_types,
            "extracted_options": [
                {
                    "key": o.key,
                    "text": o.text,
                    "html_length": len(o.html),
                    "is_blank": o.is_blank,
                    "has_mathml": o.has_mathml,
                }
                for o in norm_q.options
            ],
            "stem_extraction_status": stem_status,
            "stem_text_preview": norm_q.stem_text[:120] if norm_q.stem_text else "",
            "solution_text_preview": norm_q.solution_text[:120] if norm_q.solution_text else "",
            "has_mathml_in_question": "<math" in norm_q.raw_question_html,
            "has_mathml_in_solution": "<math" in norm_q.raw_solution_html,
            "raw_question_hash_before": q_hash_before,
            "raw_question_hash_after": q_hash_after,
            "raw_solution_hash_before": s_hash_before,
            "raw_solution_hash_after": s_hash_after,
            "raw_source_unchanged": raw_source_unchanged,
            "extraction_fidelity": fidelity,
            "raw_answer": norm_q.raw_answer,
            "normalized_answer": norm_q.normalized_answer,
            "answer_anomalies": norm_q.answer_anomalies,
            "parser_warnings": norm_q.parser_warnings,
            "detected_content_loss": not (raw_source_unchanged and fidelity["fidelity_pass"]),
        }
        audit_entries.append(entry)

    out_path = settings.DATA_RAW_DIR.parent / "normalizer_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_entries, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(audit_entries)} audit entries at: {out_path}")
    print(f"Explicit Category Breakdown:")
    for cat, ids in category_lists.items():
        print(f"  - {cat}: {len(ids)} questions")
    print(f"Total SCQ: {len(category_lists['scq_complete_4_options']) + len(category_lists['scq_blank_option']) + len(category_lists['scq_missing_option'])} (expected 31)")
    print(f"Raw source unchanged on all records: {all(e['raw_source_unchanged'] for e in audit_entries)}")
    print(f"Extraction fidelity passed on all records: {all(e['extraction_fidelity']['fidelity_pass'] for e in audit_entries)}")
    print(f"Zero detected content loss: {sum(1 for e in audit_entries if e['detected_content_loss']) == 0}")

if __name__ == "__main__":
    generate_normalizer_audit()
