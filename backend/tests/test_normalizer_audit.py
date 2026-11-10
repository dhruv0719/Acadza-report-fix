import hashlib
import json
from pathlib import Path
import pytest

from app.core.config import settings
from app.services.data_loader import load_normalized_questions, load_raw_questions
from app.services.normalizer import (
    dom_to_semantic_text,
    extract_dom_stem_and_options,
    mathml_to_text,
)


@pytest.fixture(scope="module")
def questions_data():
    raw = load_raw_questions()
    normalized = load_normalized_questions()
    raw_map = {q["_id"]: q for q in raw}
    norm_map = {q.id: q for q in normalized}
    return {"raw": raw, "normalized": normalized, "raw_map": raw_map, "norm_map": norm_map}


def test_standard_html_markers(questions_data):
    """Checks standard text option markers (A), (B), (C), (D) across multi-h3 layout."""
    norm_map = questions_data["norm_map"]
    q1 = norm_map["60ca4feb6420652745f55522"]
    assert len(q1.options) == 4
    assert [o.key for o in q1.options] == ["A", "B", "C", "D"]
    assert "100 N" in q1.options[0].text
    assert "121 N" in q1.options[1].text
    assert "99 N" in q1.options[2].text
    assert "None of these" in q1.options[3].text


def test_mathml_wrapped_markers(questions_data):
    """Checks questions with option markers wrapped inside MathML <mo> nodes."""
    norm_map = questions_data["norm_map"]
    
    # QID 68c9ae5afb6b2f16e2d43b1c has <math><mrow><mo>(A)</mo>...
    q_math = norm_map["68c9ae5afb6b2f16e2d43b1c"]
    assert len(q_math.options) == 4
    assert [o.key for o in q_math.options] == ["A", "B", "C", "D"]
    assert "3.1 V" in q_math.options[0].text
    assert "2.0 V" in q_math.options[1].text
    assert "5.1 V" in q_math.options[2].text
    assert "1.1 V" in q_math.options[3].text

    # QID 68c8153cfb6b2f16e2d3ceaf has <mo>(A)</mo> markers
    q_mcq = norm_map["68c8153cfb6b2f16e2d3ceaf"]
    assert len(q_mcq.options) == 4
    assert [o.key for o in q_mcq.options] == ["A", "B", "C", "D"]
    assert "parallel to the uniform electrostatic" in q_mcq.options[0].text


def test_nested_spans_options(questions_data):
    """Checks questions with nested spans across options."""
    norm_map = questions_data["norm_map"]

    # QID 6062ec84518e9535e120c422 has 3 levels of nested spans
    q_span = norm_map["6062ec84518e9535e120c422"]
    assert len(q_span.options) == 4
    assert [o.key for o in q_span.options] == ["A", "B", "C", "D"]
    assert "5.7" in q_span.options[0].text
    assert "0.63" in q_span.options[1].text
    assert "1.9" in q_span.options[2].text
    assert "16.1" in q_span.options[3].text

    # QID 612151a6a34397610a9a2e58 has nested spans spanning options
    q_span2 = norm_map["612151a6a34397610a9a2e58"]
    assert len(q_span2.options) == 4
    assert [o.key for o in q_span2.options] == ["A", "B", "C", "D"]
    assert "0.168 eV" in q_span2.options[0].text
    assert "16.8 eV" in q_span2.options[1].text
    assert "1.68 eV" in q_span2.options[2].text
    assert "2.5 eV" in q_span2.options[3].text


def test_blank_option_detection(questions_data):
    """Verifies Option C in Question 68e872546e45ba37dcc16bc0 is detected as blank."""
    norm_map = questions_data["norm_map"]
    q_blank = norm_map["68e872546e45ba37dcc16bc0"]
    assert len(q_blank.options) == 4
    assert [o.key for o in q_blank.options] == ["A", "B", "C", "D"]

    opt_c = q_blank.options[2]
    assert opt_c.key == "C"
    assert opt_c.is_blank is True
    assert opt_c.text == ""
    assert any("blank" in w.lower() for w in q_blank.parser_warnings)


def test_missing_option_detection(questions_data):
    """Verifies Question 622f08d7b70e4b50e4500a1b has only 3 options (D is missing)."""
    norm_map = questions_data["norm_map"]
    q_missing = norm_map["622f08d7b70e4b50e4500a1b"]
    assert len(q_missing.options) == 3
    assert [o.key for o in q_missing.options] == ["A", "B", "C"]
    assert any("Option D is missing" in w for w in q_missing.parser_warnings)


def test_repeated_and_distractor_markers(questions_data):
    """Verifies Question 695ee00b88d7701e561aabc5 ignores 'Assertion (A)' and extracts true options."""
    norm_map = questions_data["norm_map"]
    q_assertion = norm_map["695ee00b88d7701e561aabc5"]
    assert len(q_assertion.options) == 4
    assert [o.key for o in q_assertion.options] == ["A", "B", "C", "D"]

    # Option A text must be the option content, not the assertion text!
    assert "Both A and R are true, and R is the correct explanation" in q_assertion.options[0].text
    assert "Both A and R are true, but R is not the correct explanation" in q_assertion.options[1].text
    assert "A is true, but R is false" in q_assertion.options[2].text
    assert "A is false, but R is true" in q_assertion.options[3].text
    # Stem must contain the assertion
    assert "Assertion" in q_assertion.stem_text
    assert "Reason" in q_assertion.stem_text


def test_all_question_types_handling(questions_data):
    """Verifies correct separation and handling across SCQ (31), MCQ (2), and Integer (10)."""
    normalized = questions_data["normalized"]

    scqs = [q for q in normalized if q.question_type == "scq"]
    mcqs = [q for q in normalized if q.question_type == "mcq"]
    integers = [q for q in normalized if q.question_type == "integerQuestion"]

    assert len(scqs) == 31
    assert len(mcqs) == 2
    assert len(integers) == 10

    # SCQs must have options (3 or 4)
    for q in scqs:
        assert len(q.options) in (3, 4)
        assert len(q.stem_text) > 0

    # MCQs must have 4 options and preserve answer anomalies
    for q in mcqs:
        assert len(q.options) == 4
        assert len(q.answer_anomalies) > 0

    # MCQ 1 has empty string in answer list: ['', 'B']
    mcq1 = next(q for q in mcqs if q.id == "68f21caf941cda588bc04365")
    assert mcq1.raw_answer == ["", "B"]
    assert mcq1.normalized_answer == ["B"]
    assert "empty_string_in_answer_list" in mcq1.answer_anomalies

    # MCQ 2 has comma separated string in list: ['A, B, D']
    mcq2 = next(q for q in mcqs if q.id == "68c8153cfb6b2f16e2d3ceaf")
    assert mcq2.raw_answer == ["A, B, D"]
    assert mcq2.normalized_answer == ["A", "B", "D"]
    assert "comma_separated_string_in_list" in mcq2.answer_anomalies

    # Integer questions must NEVER have options extracted
    for q in integers:
        assert len(q.options) == 0
        assert q.stem_html == q.raw_question_html
        assert len(q.stem_text) > 0


def test_raw_content_preservation(questions_data):
    """Verifies zero content loss across all 43 questions via exact SHA-256 matching."""
    normalized = questions_data["normalized"]
    raw_map = questions_data["raw_map"]

    for q in normalized:
        raw_rec = raw_map[q.id]
        raw_payload = raw_rec[q.question_type]

        raw_q_str = raw_payload["question"]
        raw_s_str = raw_payload["solution"]

        # Bit-for-bit identity check
        assert q.raw_question_html == raw_q_str, f"Mismatch in raw_question_html for {q.id}"
        assert q.raw_solution_html == raw_s_str, f"Mismatch in raw_solution_html for {q.id}"
        assert q.raw_answer == raw_payload["answer"], f"Mismatch in raw_answer for {q.id}"
        assert q.raw_record == raw_rec, f"Mismatch in raw_record for {q.id}"

        # SHA-256 check
        hash_q_before = hashlib.sha256(raw_q_str.encode("utf-8")).hexdigest()
        hash_q_after = hashlib.sha256(q.raw_question_html.encode("utf-8")).hexdigest()
        assert hash_q_before == hash_q_after

        hash_s_before = hashlib.sha256(raw_s_str.encode("utf-8")).hexdigest()
        hash_s_after = hashlib.sha256(q.raw_solution_html.encode("utf-8")).hexdigest()
        assert hash_s_before == hash_s_after


def test_mathml_semantic_text_conversion():
    """Verifies that MathML is converted into readable text without regex flattening."""
    sample_mathml = """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <mrow>
        <mfrac>
          <mrow><mi>q</mi></mrow>
          <mrow><mn>2</mn></mrow>
        </mfrac>
        <mo>+</mo>
        <msup>
          <mrow><mi>r</mi></mrow>
          <mrow><mn>2</mn></mrow>
        </msup>
      </mrow>
    </math>
    """
    text = dom_to_semantic_text(sample_mathml)
    assert "(q / 2)" in text
    assert "r^2" in text


def test_normalizer_audit_file():
    """Verifies the generated data/normalizer_audit.json file integrity."""
    audit_path = settings.DATA_RAW_DIR.parent / "normalizer_audit.json"
    assert audit_path.exists(), "normalizer_audit.json does not exist"

    with open(audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert len(audit) == 43, f"Expected 43 audit entries, found {len(audit)}"

    for entry in audit:
        assert entry["raw_source_unchanged"] is True, f"Raw source modified in audit for {entry['question_id']}"
        assert entry["extraction_fidelity"]["fidelity_pass"] is True, f"Fidelity failed for {entry['question_id']}"
        assert entry["detected_content_loss"] is False, f"Content loss detected for {entry['question_id']}"

    # Verify exactly 4 entries have warnings (blank option, missing option, 2 answer anomalies)
    entries_with_warnings = [e for e in audit if len(e["parser_warnings"]) > 0]
    assert len(entries_with_warnings) == 4
    warning_qids = set(e["question_id"] for e in entries_with_warnings)
    assert warning_qids == {
        "68e872546e45ba37dcc16bc0",  # blank option C
        "622f08d7b70e4b50e4500a1b",  # missing option D
        "68f21caf941cda588bc04365",  # ['', 'B']
        "68c8153cfb6b2f16e2d3ceaf",  # ['A, B, D']
    }

