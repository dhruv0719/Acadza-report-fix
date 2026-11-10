import re
from typing import Any, Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup, Tag, NavigableString

from app.models.question import (
    ErrorHistoryEntry,
    NormalizedQuestion,
    ParsedOption,
)


def mathml_to_text(elem: Union[Tag, NavigableString]) -> str:
    """Converts a MathML DOM element to human/LLM-readable mathematical text using structured traversal.
    
    CRITICAL: Does not use regex to flatten or strip MathML. Preserves mathematical structure
    (fractions, superscripts, subscripts, roots) into semantic readable text.
    """
    if isinstance(elem, NavigableString):
        return str(elem)

    tag = elem.name.lower()
    children = [c for c in elem.children if isinstance(c, (Tag, NavigableString)) and str(c).strip()]

    if tag in ("mi", "mn", "mtext"):
        return elem.get_text(strip=True)
    elif tag == "mo":
        return elem.get_text(strip=True)
    elif tag == "mfrac":
        num = mathml_to_text(children[0]) if len(children) > 0 else ""
        den = mathml_to_text(children[1]) if len(children) > 1 else ""
        return f"({num} / {den})"
    elif tag == "msup":
        base = mathml_to_text(children[0]) if len(children) > 0 else ""
        sup = mathml_to_text(children[1]) if len(children) > 1 else ""
        return f"{base}^{sup}"
    elif tag == "msub":
        base = mathml_to_text(children[0]) if len(children) > 0 else ""
        sub = mathml_to_text(children[1]) if len(children) > 1 else ""
        return f"{base}_{sub}"
    elif tag == "msubsup":
        base = mathml_to_text(children[0]) if len(children) > 0 else ""
        sub = mathml_to_text(children[1]) if len(children) > 1 else ""
        sup = mathml_to_text(children[2]) if len(children) > 2 else ""
        return f"{base}_{sub}^{sup}"
    elif tag == "msqrt":
        inner = "".join(mathml_to_text(c) for c in children)
        return f"sqrt({inner})"
    elif tag == "mroot":
        base = mathml_to_text(children[0]) if len(children) > 0 else ""
        deg = mathml_to_text(children[1]) if len(children) > 1 else ""
        return f"root({base}, {deg})"
    elif tag in ("mtable", "mtr", "mtd", "mrow", "mstyle", "math", "semantics"):
        parts = [mathml_to_text(c) for c in children]
        return " ".join([p for p in parts if p])
    else:
        return elem.get_text(separator=" ", strip=True)


def dom_to_semantic_text(html_or_soup: Union[str, BeautifulSoup, Tag]) -> str:
    """Converts HTML with embedded MathML into clean semantic text without using regex flattening."""
    if not html_or_soup:
        return ""
    if isinstance(html_or_soup, str):
        soup = BeautifulSoup(html_or_soup, "html.parser")
    else:
        soup = html_or_soup

    # Work on a clone so the original DOM remains pristine
    soup_copy = BeautifulSoup(str(soup), "html.parser")
    for math_elem in soup_copy.find_all("math"):
        conv = mathml_to_text(math_elem)
        math_elem.replace_with(f" {conv} ")

    text = soup_copy.get_text(separator=" ", strip=True)
    return re.sub(r'\s+', ' ', text).strip()


def locate_option_markers(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Locates option marker nodes (A, B, C, D) in the DOM in sequence.
    
    Recognizes:
    - MathML <mo> nodes (e.g. <math><mrow><mo>(A)</mo>...</math>)
    - Text nodes (NavigableString) matching option patterns while ignoring
      distractors like 'Assertion (A)' or standalone math variables.
    """
    expected = ["A", "B", "C", "D"]
    markers = []
    curr_idx = 0

    for node in soup.descendants:
        if curr_idx >= len(expected):
            break
        target_key = expected[curr_idx]

        # Case 1: MathML <mo> node
        if isinstance(node, Tag) and node.name.lower() == "mo":
            txt = node.get_text(strip=True).upper()
            if txt in (f"({target_key})", target_key):
                math_parent = node.find_parent("math") or node
                markers.append({
                    "key": target_key,
                    "type": "mathml_mo",
                    "marker_node": math_parent,
                })
                curr_idx += 1
                continue

        # Case 2: Ordinary text node
        elif isinstance(node, NavigableString):
            if node.find_parent("math"):
                continue
            txt = str(node)
            pattern = rf'(?:^|[\n\r]|(?<![A-Za-z0-9_]))\({target_key}\)|\b{target_key}\s*[\.\)]'
            m = re.search(pattern, txt)
            if m:
                prefix = txt[: m.start()].strip()
                # Do not match 'Assertion (A)' as an option marker
                if "assertion" in prefix.lower():
                    continue
                markers.append({
                    "key": target_key,
                    "type": "text_node",
                    "marker_node": node,
                    "span": m.span(),
                    "matched": m.group(0),
                })
                curr_idx += 1
                continue

    return markers


def extract_dom_stem_and_options(q_html: str, qtype: str) -> Dict[str, Any]:
    """DOM-based extraction of stem and options without slicing complete HTML with regex.
    
    - Never processes integer questions for options (preserves full stem).
    - Traverses DOM to separate stem from options container.
    - Handles nested spans, inline MathML <mo> markers, and linebreaks.
    - Accurately flags blank options and missing options without fabricating content.
    """
    if qtype == "integerQuestion":
        return {
            "stem_html": q_html,
            "stem_text": dom_to_semantic_text(q_html),
            "options": [],
            "marker_types": [],
            "warnings": [],
            "status": "integer_no_options",
        }

    soup = BeautifulSoup(q_html, "html.parser")
    markers = locate_option_markers(soup)

    if len(markers) < 2:
        return {
            "stem_html": q_html,
            "stem_text": dom_to_semantic_text(q_html),
            "options": [],
            "marker_types": [],
            "warnings": ["Insufficient option markers detected in SCQ/MCQ"],
            "status": "fallback_insufficient_markers",
        }

    marker_types = sorted(list(set(m["type"] for m in markers)))
    marker_keys = [m["key"] for m in markers]
    warnings = []

    if "D" not in marker_keys and len(marker_keys) == 3:
        warnings.append("Option D is missing from question (only A, B, C present)")

    first_marker = markers[0]
    top_h3s = [c for c in soup.contents if isinstance(c, Tag) and c.name.lower() == "h3"]

    # Layout extraction
    if len(top_h3s) >= 2 and any(
        m["marker_node"] in top_h3s[1].descendants or m["marker_node"] == top_h3s[1]
        for m in markers
    ):
        # Two-h3 layout: stem is the first h3
        stem_html = str(top_h3s[0]).strip()
        stem_text = dom_to_semantic_text(top_h3s[0])
    else:
        # Single container layout: nodes before marker A are stem
        container = top_h3s[0] if top_h3s else soup
        stem_children = []
        for child in container.children:
            if child == first_marker["marker_node"] or (
                isinstance(child, Tag) and first_marker["marker_node"] in child.descendants
            ):
                break
            stem_children.append(str(child))
        stem_inner = "".join(stem_children).rstrip()
        stem_inner = re.sub(r'(?:<br\s*/?>\s*)+$', '', stem_inner).strip()
        stem_html = f"<h3>{stem_inner}</h3>" if stem_inner else ""
        stem_text = dom_to_semantic_text(stem_html)

    # In-order DOM traversal of descendants to collect each option's content
    all_descendants = list(soup.descendants)
    options: List[ParsedOption] = []

    for i, m in enumerate(markers):
        key = m["key"]
        next_m = markers[i + 1] if i + 1 < len(markers) else None

        opt_text_parts = []
        opt_html_parts = []

        m_node = m["marker_node"]
        if m["type"] == "text_node":
            txt = str(m_node)
            start_span, end_span = m["span"]
            after_marker = txt[end_span:]
            if after_marker:
                opt_text_parts.append(after_marker)
                opt_html_parts.append(after_marker)
        elif m["type"] == "mathml_mo":
            # Marker was the <math> node itself; content follows
            pass

        m_idx = all_descendants.index(m_node)
        next_idx = all_descendants.index(next_m["marker_node"]) if next_m else len(all_descendants)

        for d_idx in range(m_idx + 1, next_idx):
            d = all_descendants[d_idx]
            if isinstance(d, Tag) and d.name.lower() == "math":
                conv = mathml_to_text(d)
                opt_text_parts.append(f" {conv} ")
                opt_html_parts.append(str(d))
            elif isinstance(d, Tag) and d.name.lower() == "br":
                opt_text_parts.append(" ")
                opt_html_parts.append("<br />")
            elif isinstance(d, NavigableString):
                if d.find_parent("math"):
                    continue
                opt_text_parts.append(str(d))
                opt_html_parts.append(str(d))

        raw_text = "".join(opt_text_parts)
        cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()
        cleaned_html = "".join(opt_html_parts).strip()
        cleaned_html = re.sub(r'^(?:<br\s*/?>\s*)+', '', cleaned_html).strip()
        cleaned_html = re.sub(r'(?:<br\s*/?>\s*)+$', '', cleaned_html).strip()

        is_blank = (len(cleaned_text) == 0)
        if is_blank:
            warnings.append(f"Option {key} has blank/empty content")

        options.append(
            ParsedOption(
                key=key,
                html=cleaned_html,
                text=cleaned_text,
                is_blank=is_blank,
                has_mathml=("<math" in cleaned_html),
            )
        )

    return {
        "stem_html": stem_html,
        "stem_text": stem_text,
        "options": options,
        "marker_types": marker_types,
        "warnings": warnings,
        "status": "success",
    }


def detect_answer_anomalies(raw_answer: Any, qtype: str) -> Tuple[Union[str, List[str]], List[str]]:
    """Normalizes raw answer while explicitly capturing production defects and anomalies."""
    anomalies: List[str] = []

    if raw_answer is None:
        anomalies.append("answer_is_none")
        return "", anomalies

    if qtype == "mcq":
        if not isinstance(raw_answer, list):
            anomalies.append("mcq_answer_not_a_list")
            interpreted = [s.strip().upper() for s in str(raw_answer).split(",") if s.strip()]
            return interpreted, anomalies

        interpreted_items = []
        for item in raw_answer:
            if item == "":
                anomalies.append("empty_string_in_answer_list")
            elif isinstance(item, str) and "," in item:
                anomalies.append("comma_separated_string_in_list")
                parts = [p.strip().upper() for p in item.split(",") if p.strip()]
                interpreted_items.extend(parts)
            else:
                val = str(item).strip().upper()
                if val:
                    interpreted_items.append(val)
        return sorted(list(set(interpreted_items))), anomalies

    elif qtype == "scq":
        if not isinstance(raw_answer, str):
            anomalies.append(f"scq_answer_not_string_{type(raw_answer).__name__}")
            ans_str = str(raw_answer).strip().upper()
        else:
            ans_str = raw_answer.strip().upper()

        if len(ans_str) != 1 or ans_str not in ("A", "B", "C", "D"):
            anomalies.append(f"scq_answer_non_standard_{ans_str}")
        return ans_str, anomalies

    elif qtype == "integerQuestion":
        ans_str = str(raw_answer).strip()
        if not ans_str.isdigit():
            anomalies.append(f"integer_answer_non_digit_{ans_str}")
        return ans_str, anomalies

    return str(raw_answer).strip(), anomalies


def check_figure_reference(text: str) -> bool:
    """Checks if text contains references to figures or diagrams."""
    pattern = re.compile(r'\b(fig|figure|diagram|shown in figure|as shown)\b', re.IGNORECASE)
    return bool(pattern.search(text))


def normalize_question(raw: Dict[str, Any], report_ids: Optional[List[str]] = None) -> NormalizedQuestion:
    """Converts raw JSON question dictionary into a NormalizedQuestion model.
    
    CRITICAL: Preserves original HTML, MathML, raw answer, and full record
    completely intact in raw_question_html, raw_solution_html, and raw_record
    without stripping or loss.
    """
    qtype = raw.get("questionType", "scq")
    payload = raw.get(qtype, {})

    raw_question_html = payload.get("question", "")
    raw_solution_html = payload.get("solution", "")
    raw_answer = payload.get("answer")

    dom_res = extract_dom_stem_and_options(raw_question_html, qtype)
    norm_answer, answer_anomalies = detect_answer_anomalies(raw_answer, qtype)

    all_warnings = list(dom_res["warnings"])
    if answer_anomalies:
        all_warnings.extend([f"Answer anomaly: {a}" for a in answer_anomalies])

    error_history = [
        ErrorHistoryEntry.model_validate(eh)
        for eh in raw.get("errorHistory", [])
    ]

    has_mathml = ("<math" in raw_question_html) or ("<math" in raw_solution_html)
    has_figure = check_figure_reference(raw_question_html) or check_figure_reference(raw_solution_html)

    solution_text = dom_to_semantic_text(raw_solution_html)

    return NormalizedQuestion(
        id=raw.get("_id"),
        qid=raw.get("qid"),
        question_type=qtype,
        subject=raw.get("subject", ""),
        chapter=raw.get("chapter", ""),
        concept=raw.get("concept"),
        sub_concept=raw.get("subConcept"),
        level=raw.get("level"),
        updated_at=raw.get("updatedAt"),
        error_flag=raw.get("error", 1),
        error_history=error_history,
        raw_question_html=raw_question_html,
        raw_solution_html=raw_solution_html,
        stem_html=dom_res["stem_html"],
        stem_text=dom_res["stem_text"],
        solution_text=solution_text,
        options=dom_res["options"],
        raw_answer=raw_answer,
        normalized_answer=norm_answer,
        answer_anomalies=answer_anomalies,
        parser_warnings=all_warnings,
        ques_images=payload.get("quesImages", []),
        solution_images=payload.get("solutionImages", []),
        has_mathml=has_mathml,
        has_figure_reference=has_figure,
        report_ids=report_ids or [],
        raw_record=raw,
    )
