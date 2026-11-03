"""Master Quality Assurance and Zero-Intersection Verification Test Suite for EduAdapt.

Verifies:
1. Strict Question Counts: |P| = 5, |A| = 10 for every PPS topic.
2. Mathematical Zero-Intersection Invariant: P ∩ A = ∅ (Exact & Semantic Near-Duplicates).
3. Authoritative Backend Practice MCQ Generation and Submission Evaluation.
4. Authoritative Backend Formal Assessment Generation, Submission Evaluation, and Roadmap Progression.
5. Multi-Mermaid Diagram Extraction and Independent Validation.
6. Multi-Student Profile Isolation (S001, S005).
"""

import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.services.question_bank import (
    PRACTICE_BANK,
    ASSESSMENT_BANK,
    get_practice_questions,
    get_assessment_questions,
    verify_topic_zero_intersection,
    verify_all_topics_zero_intersection,
    calculate_jaccard_similarity,
    normalize_text,
)
from eduadapt.services.question_service import QuestionService, PPS_CURRICULUM_SEQUENCE
from eduadapt.teaching.diagrams import MermaidValidator, DiagramResult


client = TestClient(app)


# ==============================================================================
# TEST 1: STRICT QUESTION COUNT & ZERO-INTERSECTION VERIFICATION ACROSS ALL TOPICS
# ==============================================================================
@pytest.mark.parametrize("topic", list(PRACTICE_BANK.keys()))
def test_topic_question_count_and_zero_intersection(topic: str):
    """Verify |P|=5, |A|=10, and P ∩ A = ∅ for every PPS topic."""
    p_qs = get_practice_questions(topic, 5)
    a_qs = get_assessment_questions(topic, 10)

    # 1. Exact counts
    assert len(p_qs) == 5, f"Topic '{topic}' must have exactly 5 practice questions."
    assert len(a_qs) == 10, f"Topic '{topic}' must have exactly 10 assessment questions."

    # 2. Check each question schema: 4 options, 1 correct option, explanation, concept, difficulty
    for q in p_qs + a_qs:
        assert len(q["options"]) == 4, f"Question {q['id']} must have exactly 4 options."
        assert q["correct_option"] in ("A", "B", "C", "D"), f"Question {q['id']} correct_option must be A, B, C, or D."
        assert q["explanation"].strip() != "", f"Question {q['id']} must have a non-empty explanation."
        assert q["concept"].strip() != "", f"Question {q['id']} must have a concept tag."
        assert q["difficulty"] in ("Beginner", "Intermediate", "Advanced")

    # 3. Zero ID intersection
    p_ids = {q["id"] for q in p_qs}
    a_ids = {q["id"] for q in a_qs}
    assert p_ids.intersection(a_ids) == set(), f"Topic '{topic}' has ID intersection: {p_ids & a_ids}"

    # 4. Zero exact normalized text intersection
    p_texts = {normalize_text(q["question"]) for q in p_qs}
    a_texts = {normalize_text(q["question"]) for q in a_qs}
    assert p_texts.intersection(a_texts) == set(), f"Topic '{topic}' has exact text intersection: {p_texts & a_texts}"

    # 5. Zero semantic near-duplicate intersection (Jaccard similarity < 0.65)
    for p in p_qs:
        for a in a_qs:
            sim = calculate_jaccard_similarity(p["question"], a["question"])
            assert sim < 0.65, (
                f"Topic '{topic}' has high semantic near-duplicate similarity ({sim:.2f}) between:\n"
                f"  Practice: {p['question']}\n"
                f"  Assessment: {a['question']}"
            )


def test_all_topics_zero_intersection_runner():
    """Verify all topics pass the zero intersection validator."""
    results = verify_all_topics_zero_intersection()
    for topic, (passed, msg) in results.items():
        assert passed is True, f"Failed zero intersection for {topic}: {msg}"


# ==============================================================================
# TEST 2: AUTHORITATIVE PRACTICE MCQ API ENDPOINTS
# ==============================================================================
def test_practice_mcq_get_endpoint():
    """Verify GET /api/practice/{student_id}/{topic}/mcqs returns exactly 5 questions."""
    resp = client.get("/api/practice/S001/Pointers/mcqs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "S001"
    assert data["topic"] == "Pointers"
    assert data["total_questions"] == 5
    assert len(data["questions"]) == 5
    for q in data["questions"]:
        assert len(q["options"]) == 4
        assert q["concept"] != ""


def test_practice_mcq_authoritative_backend_submission():
    """Verify POST /api/practice/submit authoritatively evaluates answers and updates Learning Twin."""
    # Submit all correct answers
    p_qs = get_practice_questions("Pointers", 5)
    correct_answers = {str(idx): q["correct_option"] for idx, q in enumerate(p_qs)}

    resp = client.post("/api/practice/submit", json={
        "student_id": "S001",
        "topic": "Pointers",
        "answers": correct_answers,
        "time_taken_seconds": 30,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 100
    assert data["accuracy"] == 1.0
    assert data["correct_count"] == 5
    assert data["total_questions"] == 5
    assert data["is_correct"] is True
    assert data["weak_concepts"] == []
    assert len(data["results"]) == 5

    # Submit partial answers with deliberate mistake to test weak concepts identification
    partial_answers = {
        "0": p_qs[0]["correct_option"],
        "1": "D" if p_qs[1]["correct_option"] != "D" else "A",  # Wrong
        "2": p_qs[2]["correct_option"],
        "3": p_qs[3]["correct_option"],
        "4": p_qs[4]["correct_option"],
    }
    resp2 = client.post("/api/practice/submit", json={
        "student_id": "S001",
        "topic": "Pointers",
        "answers": partial_answers,
        "time_taken_seconds": 45,
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["score"] == 80
    assert data2["correct_count"] == 4
    assert len(data2["weak_concepts"]) > 0
    assert p_qs[1]["concept"] in data2["weak_concepts"]


# ==============================================================================
# TEST 3: AUTHORITATIVE FORMAL ASSESSMENT API & ROADMAP PROGRESSION
# ==============================================================================
def test_assessment_get_endpoint_returns_10_questions():
    """Verify GET /api/assessment/{student_id}/{topic}/all returns exactly 10 questions."""
    resp = client.get("/api/assessment/S001/Pointers/all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_questions"] == 10
    assert len(data["questions"]) == 10
    # Confirm zero intersection with practice for this topic
    p_resp = client.get("/api/practice/S001/Pointers/mcqs")
    p_ids = {q["id"] for q in p_resp.json()["questions"]}
    a_ids = {q["id"] for q in data["questions"]}
    assert p_ids.intersection(a_ids) == set()


def test_assessment_submission_and_roadmap_progression():
    """Verify assessment submission with >= 60% unlocks next topic and updates roadmap."""
    a_qs = get_assessment_questions("Pointers", 10)
    # 8 correct out of 10 (80% score)
    answers = {}
    for idx, q in enumerate(a_qs):
        if idx < 8:
            answers[str(idx)] = q["correct_option"]
        else:
            answers[str(idx)] = "D" if q["correct_option"] != "D" else "A"

    resp = client.post("/api/assessment/submit", json={
        "student_id": "S001",
        "topic": "Pointers",
        "answers": answers,
        "time_taken_seconds": 120,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 80
    assert data["correct_count"] == 8
    assert data["total_questions"] == 10
    assert data["mastery_achieved"] is True
    assert data["completed_topic"] == "Pointers"
    assert data["next_topic"] == "Structures"

    # Verify roadmap endpoint reflects progression
    roadmap_resp = client.get("/api/roadmap/S001")
    assert roadmap_resp.status_code == 200
    rm = roadmap_resp.json()
    assert "Pointers" in rm["completed_topics"]


def test_assessment_low_score_recommends_remediation_without_trap():
    """Verify low score (< 60%) does not achieve mastery but advises remediation without locking student."""
    a_qs = get_assessment_questions("Loops", 10)
    # Only 3 correct answers (30% score)
    answers = {str(idx): "A" for idx in range(10)}

    resp = client.post("/api/assessment/submit", json={
        "student_id": "S005",
        "topic": "Loops",
        "answers": answers,
        "time_taken_seconds": 90,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["mastery_achieved"] is False
    assert data["score"] < 60
    assert len(data["weak_concepts"]) > 0
    assert "revising" in data["feedback"].lower() or "practice" in data["feedback"].lower()


# ==============================================================================
# TEST 4: MULTIPLE MERMAID DIAGRAM EXTRACTION AND INDEPENDENT VALIDATION
# ==============================================================================
def test_multiple_mermaid_diagrams_extracted_and_rendered():
    """Verify that if GenAI returns N Mermaid diagrams, all N are extracted and validated independently."""
    sample_multi_diagram_markdown = (
        "### Visual Architecture Diagram\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    A[Variable a = 42] --> B[Pointer *ptr = &a]\n"
        "```\n\n"
        "Next, here is the execution and dereferencing cycle:\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    Start[\"Read *ptr\"] --> Address[\"Look up 0x1000\"]\n"
        "    Address --> Value[\"Retrieve Integer 42\"]\n"
        "```\n"
    )

    blocks = MermaidValidator.extract_all_mermaid_blocks(sample_multi_diagram_markdown)
    assert len(blocks) == 2, f"Expected 2 extracted diagrams, got {len(blocks)}"

    results = MermaidValidator.validate_and_sanitize_all(blocks, topic="Pointers")
    assert len(results) == 2
    for r in results:
        assert isinstance(r, DiagramResult)
        assert r.is_valid is True
        assert "flowchart TD" in r.mermaid_code


def test_one_broken_diagram_does_not_break_other_diagrams():
    """Verify that an invalid diagram does not crash or invalidate adjacent diagrams."""
    raw_blocks = [
        "flowchart TD\n    A[\"Valid Node A\"] --> B[\"Valid Node B\"]",
        "flowchart TD\n    Unclosed bracket [ --> B",  # Deliberate bracket syntax error
        "flowchart TD\n    C[\"Valid Node C\"] --> D[\"Valid Node D\"]",
    ]

    results = MermaidValidator.validate_and_sanitize_all(raw_blocks, topic="Arrays")
    assert len(results) == 3
    # Diagram 1 is valid
    assert results[0].is_valid is True
    # Diagram 2 is caught safely with validation_error
    assert results[1].is_valid is False
    assert results[1].validation_error is not None
    # Diagram 3 remains completely valid
    assert results[2].is_valid is True


# ==============================================================================
# TEST 5: MULTI-STUDENT PROFILE ISOLATION
# ==============================================================================
def test_multi_student_data_isolation():
    """Verify Student S001 and Student S005 maintain independent state and history."""
    p1 = client.get("/api/student/S001").json()
    p5 = client.get("/api/student/S005").json()

    assert p1["student_id"] == "S001"
    assert p5["student_id"] == "S005"

    # Submit practice for S005 on Arrays
    resp = client.post("/api/practice/submit", json={
        "student_id": "S005",
        "topic": "Arrays",
        "answers": {"0": "B", "1": "B", "2": "A", "3": "B", "4": "C"},
        "time_taken_seconds": 50,
    })
    assert resp.status_code == 200

    qs = QuestionService()
    history = qs._load_history()
    assert "S005" in history
    s005_hist = history["S005"].get("practice", [])
    assert any(h["topic"] == "Arrays" for h in s005_hist)


# ==============================================================================
# TEST 6: MERMAID SANITIZATION & ARROW REPAIR
# ==============================================================================
def test_mermaid_arrow_and_unbracketed_node_repair():
    """Verify malformed arrows like --|> and unbracketed multi-token names are safely repaired."""
    malformed_source = (
        "flowchart TD\n"
        "String[\"Array of characters\"]\n"
        "String --> Character[\"ASCII Character or '\\0'\"]\n"
        "Character --|> Memory Cell"
    )
    res = MermaidValidator.validate_and_sanitize(malformed_source, topic="Strings")
    assert res.is_valid is True
    # --|> must be converted to -->
    assert "--|>" not in res.mermaid_code
    assert "-->" in res.mermaid_code
    # Multi-token node after arrow must be quoted/bracketed
    assert "Memory_Cell[\"Memory Cell\"]" in res.mermaid_code or "[\"Memory Cell\"]" in res.mermaid_code


# ==============================================================================
# TEST 7: C COMPILATION DIAGNOSTICS & WRONG ANSWER DIAGNOSIS
# ==============================================================================
def test_c_compilation_error_diagnostics():
    """Verify compilation failure captures raw GCC stderr diagnostic and returns COMPILATION_ERROR status."""
    bad_code = "int main() { printf(Missing semicolon) return 0; }"
    resp = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Pointers",
        "source_code": bad_code,
        "is_submission": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPILATION_ERROR"
    assert data["compiler_output"] != ""
    assert "error:" in data["compiler_output"]


def test_c_wrong_answer_output_comparison():
    """Verify wrong output returns WRONG_ANSWER status with actual and expected outputs."""
    code = '#include <stdio.h>\nint main() { printf("Actual 123\\n"); return 0; }'
    resp = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Arrays",
        "source_code": code,
        "expected_output": "Expected 456",
        "is_submission": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "WRONG_ANSWER"
    assert data["passed"] is False
    assert "Actual 123" in data["actual_output"]
    assert data["expected_output"] == "Expected 456"


def test_c_code_with_scanf_handles_stdin_without_hanging():
    """Verify code using scanf executes with stdin_input or EOF immediately without timeout."""
    code = (
        "#include <stdio.h>\n"
        "#include <stdlib.h>\n"
        "int main() {\n"
        "    int size;\n"
        "    if (scanf(\"%d\", &size) != 1) return 0;\n"
        "    printf(\"Size read: %d\\n\", size);\n"
        "    return 0;\n"
        "}"
    )
    resp = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "source_code": code,
        "stdin_input": "42\n",
        "expected_output": "Size read: 42",
        "is_submission": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED"
    assert data["passed"] is True
    assert "Size read: 42" in data["actual_output"]
    assert data["execution_time_seconds"] < 2.0
