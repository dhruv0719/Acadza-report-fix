from app.api.routes import (
    FacultyReviewRequest,
    get_all_faculty_reviews,
    get_quality_findings,
    get_question,
    get_report,
    get_result,
    get_taxonomy,
    get_telemetry,
    get_unreported_audit,
    health_check,
    list_grouped_reports,
    list_questions,
    list_reports,
    list_results,
    submit_faculty_review,
)


def test_health_endpoint():
    data = health_check()
    assert data["status"] == "healthy"
    assert data["questions_count"] == 43
    assert data["reports_count"] == 44
    assert data["results_count"] == 44


def test_taxonomy_endpoint():
    data = get_taxonomy()
    assert "verdicts" in data
    assert "repairs" in data
    assert len(data["verdicts"]) == 7
    assert len(data["repairs"]) == 18


def test_questions_endpoint():
    questions = list_questions()
    assert len(questions) == 43

    # Test filtering by question_type
    scqs = list_questions(question_type="scq")
    assert len(scqs) == 31

    # Single question
    q0 = get_question(questions[0].id)
    assert q0.id == questions[0].id


def test_reports_endpoint():
    reports = list_reports()
    assert len(reports) == 44

    r004 = get_report("R004")
    assert r004.reportId == "R004"

    grouped = list_grouped_reports()
    assert len(grouped) == 39


def test_results_endpoint():
    results = list_results()
    assert len(results) == 44

    # Test filtering by route
    auto_items = list_results(route="auto_apply")
    assert len(auto_items) == 17
    assert all(i.route == "auto_apply" for i in auto_items)

    faculty_items = list_results(route="faculty_review")
    assert len(faculty_items) == 10

    no_change_items = list_results(route="no_change")
    assert len(no_change_items) == 17


def test_get_single_result():
    r004 = get_result("R004")
    assert r004.reportId == "R004"
    assert r004.questionId == "68e870ef42c06737d6e565c4"
    assert r004.verdict == "defect"
    assert r004.repair == "answer_key"
    assert r004.route == "auto_apply"
    assert r004.edit.field == "answer"
    assert r004.edit.find == "A"
    assert r004.edit.replace == "D"


def test_quality_findings_endpoint():
    findings = get_quality_findings()
    assert len(findings) == 14
    # Check that high severity and critical findings are present
    assert any(f["question_id"] == "60f744b3f1b9bc7cc7b4a949" for f in findings)


def test_unreported_audit_endpoint():
    unreported = get_unreported_audit()
    assert len(unreported) == 4
    ids = [u["question_id"] for u in unreported]
    assert "68dea657387eea3d0d95f54a" in ids
    assert "68dea6e6387eea3d0d95f6f8" in ids
    assert "68dea87d387eea3d0d95fbe3" in ids
    assert "695ede2a88d7701e561aa9d9" in ids


def test_telemetry_endpoint():
    data = get_telemetry()
    assert "summary" in data
    assert "logs" in data
    assert data["summary"]["provider"] == "Groq"
    assert data["summary"]["total_calls"] >= 12
    assert data["summary"]["total_tokens"] >= 36000


def test_faculty_review_flow():
    from app.models.result import ProposedEdit

    # 1. Test approve
    req_approve = FacultyReviewRequest(
        action="approve",
        reviewer_notes="Verified wave interference assertion independently.",
        reviewer_name="Dr. Sharma",
    )
    res_approve = submit_faculty_review("R034", req_approve)
    assert res_approve.report_id == "R034"
    assert res_approve.status == "approved_staged"
    assert res_approve.reviewer_name == "Dr. Sharma"
    assert res_approve.reviewed_at is not None

    reviews_after_approve = get_all_faculty_reviews()
    assert "R034" in reviews_after_approve
    assert reviews_after_approve["R034"]["action"] == "approve"
    assert reviews_after_approve["R034"]["status"] == "approved_staged"

    # 2. Test reject
    req_reject = FacultyReviewRequest(
        action="reject",
        reviewer_notes="Student suggestion is mathematically incorrect.",
        reviewer_name="Prof. Verma",
    )
    res_reject = submit_faculty_review("R027", req_reject)
    assert res_reject.report_id == "R027"
    assert res_reject.status == "rejected"
    assert res_reject.reviewer_name == "Prof. Verma"

    reviews_after_reject = get_all_faculty_reviews()
    assert "R027" in reviews_after_reject
    assert reviews_after_reject["R027"]["action"] == "reject"

    # 3. Test modify
    req_modify = FacultyReviewRequest(
        action="modify",
        reviewer_notes="Adjusted surgical find string for precise DOM replacement.",
        reviewer_name="Dr. Sharma",
        modified_edit=ProposedEdit(field="answer", find="A", replace="D"),
        custom_reply="Verified: correct answer key has been staged to Option D.",
    )
    res_modify = submit_faculty_review("R004", req_modify)
    assert res_modify.report_id == "R004"
    assert res_modify.status == "modified_staged"
    assert res_modify.new_value == "D"
    assert res_modify.previous_value == "D" or res_modify.previous_value == "A"
    assert res_modify.custom_reply is not None

    reviews_after_modify = get_all_faculty_reviews()
    assert "R004" in reviews_after_modify
    assert reviews_after_modify["R004"]["action"] == "modify"
    assert len(reviews_after_modify["R004"]["history"]) >= 1
