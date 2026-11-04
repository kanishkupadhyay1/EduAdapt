"""Targeted End-to-End Validation Tests for Master Fix Prompt.

Validates:
1. AI Tutor topic-specific chat persistence and clear history.
2. C Sandbox 30.0s execution timeout and stdin detection.
3. Coding challenge competitive-programming specifications across all 10 topics.
"""

from fastapi.testclient import TestClient
import pytest
from eduadapt.api import app
from eduadapt.services.tutor_history_service import TutorHistoryService
from eduadapt.teaching.response_schema import _get_challenge_defaults, normalize_topic_name
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus

client = TestClient(app)


def test_tutor_history_persistence_and_isolation(tmp_path):
    """Test that tutor history persists per student and is isolated by topic."""
    history_file = tmp_path / "tutor_history.json"
    service = TutorHistoryService(history_file=history_file)

    # 1. Append messages for Student S001 on 'Pointers'
    service.append_message("S001", "Pointers", "student", "What is an address-of operator?")
    service.append_message("S001", "Pointers", "assistant", "The & operator retrieves the memory location of a variable.")

    # 2. Append messages for Student S001 on 'Arrays'
    service.append_message("S001", "Arrays", "student", "What is index 0 in an array?")
    service.append_message("S001", "Arrays", "assistant", "In C, arrays are zero-indexed.")

    # 3. Verify topic isolation
    pointers_hist = service.get_history("S001", "Pointers")
    arrays_hist = service.get_history("S001", "Arrays")
    loops_hist = service.get_history("S001", "Loops")

    assert len(pointers_hist) == 2
    assert pointers_hist[0]["text"] == "What is an address-of operator?"
    assert len(arrays_hist) == 2
    assert arrays_hist[0]["text"] == "What is index 0 in an array?"
    assert len(loops_hist) == 0

    # 4. Clear 'Pointers' topic only
    cleared = service.clear_topic_history("S001", "Pointers")
    assert cleared is True
    assert len(service.get_history("S001", "Pointers")) == 0
    # Arrays history remains completely intact!
    assert len(service.get_history("S001", "Arrays")) == 2


def test_tutor_history_api_endpoints():
    """Verify GET and DELETE /api/tutor/history endpoints."""
    # Add dummy message via API
    res = client.get("/api/tutor/history/S001/Pointers")
    assert res.status_code == 200
    data = res.json()
    assert "messages" in data
    assert data["student_id"] == "S001"
    assert data["topic"] == "Pointers"

    # Delete topic history
    del_res = client.delete("/api/tutor/history/S001/Pointers")
    assert del_res.status_code == 200
    assert del_res.json()["messages"] == []


def test_all_10_topics_coding_challenge_specifications():
    """Verify that all 10 PPS topics have complete competitive-programming specifications."""
    topics = [
        "Variables and Data Types",
        "Operators and Expressions",
        "Conditionals",
        "Loops",
        "Arrays",
        "Strings",
        "Functions",
        "Pointers",
        "Structures",
        "Dynamic Memory Allocation",
    ]

    for topic in topics:
        defaults = _get_challenge_defaults(topic)
        assert "title" in defaults, f"Missing title in {topic}"
        assert "problem_statement" in defaults, f"Missing problem_statement in {topic}"
        assert "input_format" in defaults, f"Missing input_format in {topic}"
        assert "output_format" in defaults, f"Missing output_format in {topic}"
        assert "constraints" in defaults, f"Missing constraints in {topic}"
        assert "starter_code" in defaults, f"Missing starter_code in {topic}"
        assert "expected_test_cases" in defaults, f"Missing expected_test_cases in {topic}"
        assert len(defaults["expected_test_cases"]) >= 1, f"Empty expected_test_cases in {topic}"
        assert "hidden_test_cases" in defaults, f"Missing hidden_test_cases in {topic}"
        assert "hints" in defaults, f"Missing hints in {topic}"
        assert len(defaults["hints"]) == 4, f"Hint ladder must have 4 tiers in {topic}"


def test_c_sandbox_timeout_configuration():
    """Verify CExecutor default timeout is 30.0s and timeout reports clean diagnostics."""
    executor = CExecutor()
    assert executor.default_timeout_seconds == 30.0

    if executor.has_compiler():
        # Code with an intentional infinite loop tested with short timeout
        infinite_loop_code = """
        #include <stdio.h>
        int main(void) {
            while (1) {}
            return 0;
        }
        """
        res = executor.execute_student_code(infinite_loop_code, timeout_seconds=1.0)
        assert res.status == ExecutionStatus.TIMEOUT
        assert "Execution timed out after" in res.notes


def test_execute_practice_code_api_timeout_and_stdin_notice():
    """Verify the /api/practice/execute endpoint passes timeout and detects missing stdin."""
    code_reading_stdin = """
    #include <stdio.h>
    int main(void) {
        int x;
        if (scanf("%d", &x) == 1) {
            printf("%d\\n", x * 2);
        }
        return 0;
    }
    """
    res = client.post(
        "/api/practice/execute",
        json={
            "student_id": "S001",
            "topic": "Variables and Data Types",
            "source_code": code_reading_stdin,
            "stdin_input": "",  # Missing stdin
            "timeout_seconds": 30.0,
            "is_submission": False,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["timeout_limit_seconds"] == 30.0
    assert "Notice: Your C program reads from standard input" in data["diagnostic_message"] or "Notice: Your C program reads from standard input" in data["notes"]
