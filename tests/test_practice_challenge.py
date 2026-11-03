"""Unit tests for the AI Coding Challenge generation, parsing, and execution pipeline.

Verifies:
1. ResponseParser.parse_coding_challenge parses markdown and JSON formats.
2. Extraction of problem statement, input/output specifications, starter C code, expected output, and 4-tier hint ladder.
3. Adaptive personalization values for students (S001 Advanced vs S005 Beginner).
4. CExecutor.execute_student_code compiles and executes student C code with process isolation and timeout.
5. Compilation errors and runtime errors are properly captured.
6. Execution API endpoint /api/practice/execute evaluates runs and submissions correctly.
"""

import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.inference.base import GenerationResult
from eduadapt.teaching.response_schema import ResponseParser


def test_parse_coding_challenge_structured():
    """Verify that ResponseParser accurately extracts all required fields from markdown challenge text."""
    sample_text = """### Title: Reverse an Array using Pointers
### Problem Statement:
Write a C program to reverse an array of integers in-place using two pointer variables.
- **Input Format**: Space-separated integers representing array elements.
- **Output Format**: Space-separated reversed integers.
- **Constraints**: In-place reversal only. No secondary array.
- **Sample Input**: 1 2 3 4 5
- **Sample Output**: 5 4 3 2 1
- **Explanation**: The elements at the start and end pointers are swapped progressively.

### Starter Code:
```c
#include <stdio.h>

void reverse_array(int *arr, int n) {
    // TODO: implement reverse
}

int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    reverse_array(arr, 5);
    for (int i = 0; i < 5; i++) {
        printf("%d%s", arr[i], i == 4 ? "" : " ");
    }
    printf("\\n");
    return 0;
}
```

### Expected Output:
5 4 3 2 1

### Hint Ladder:
- **Hint 1 (Conceptual Guidance)**: Pointers store memory addresses. You can use two pointers pointing to the start and end of the array.
- **Hint 2 (Approach)**: Initialize `left = arr` and `right = arr + n - 1`.
- **Hint 3 (Algorithmic Guidance)**: While `left < right`, swap the values at `*left` and `*right`, then advance `left++` and decrement `right--`.
- **Hint 4 (Implementation / Pseudocode)**: Use a temporary variable: `int temp = *left; *left = *right; *right = temp;`.
"""

    res = ResponseParser.parse_coding_challenge(
        raw_text=sample_text,
        topic="Pointers",
        difficulty="Advanced",
        mastery_tier="Advanced",
    )

    assert res["title"] == "Reverse an Array using Pointers"
    assert "reverse an array" in res["problem_statement"].lower()
    assert res["input_format"] == "Space-separated integers representing array elements."
    assert res["output_format"] == "Space-separated reversed integers."
    assert "In-place" in res["constraints"]
    assert res["sample_input"] == "1 2 3 4 5"
    assert res["sample_output"] == "5 4 3 2 1"
    assert "start and end pointers" in res["sample_explanation"]
    assert "#include <stdio.h>" in res["starter_code"]
    assert "void reverse_array" in res["starter_code"]
    assert res["expected_output"] == "5 4 3 2 1"
    assert len(res["hints"]) == 4
    assert "store memory addresses" in res["hint_1"]
    assert "left < right" in res["hint_3"]
    assert "int temp" in res["hint_4"]


def test_parse_coding_challenge_fallback():
    """Verify that unformatted or raw LLM output gets sensible, non-empty fallbacks."""
    raw = "Here is a quick exercise to practice pointers. Write a program to swap values."
    res = ResponseParser.parse_coding_challenge(
        raw_text=raw,
        topic="Pointers",
        difficulty="Easy",
        mastery_tier="Beginner",
    )

    assert res["title"] != ""
    assert res["topic"] == "Pointers"
    assert res["starter_code"] != ""
    assert len(res["hints"]) >= 4
    assert res["hint_1"] != ""
    assert res["hint_4"] != ""


def test_execute_student_code_success():
    """Verify that CExecutor compiles and executes valid student C code."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("C compiler not available")

    c_code = """#include <stdio.h>
int main() {
    printf("42\\n");
    return 0;
}
"""
    res = executor.execute_student_code(c_code)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.exit_code == 0
    assert "42" in res.stdout
    assert res.execution_time_seconds is not None
    assert res.execution_time_seconds >= 0.0


def test_execute_student_code_compilation_error():
    """Verify that compilation errors in student code are captured cleanly."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("C compiler not available")

    invalid_code = """#include <stdio.h>
int main() {
    this_is_a_syntax_error;;
    return 0;
}
"""
    res = executor.execute_student_code(invalid_code)
    assert res.status == ExecutionStatus.COMPILATION_ERROR
    assert res.compiler_output != ""
    assert "error" in res.compiler_output.lower()


def test_execute_student_code_timeout():
    """Verify that infinite loops in student code are terminated by the timeout."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("C compiler not available")

    infinite_loop_code = """#include <stdio.h>
int main() {
    while (1) {}
    return 0;
}
"""
    res = executor.execute_student_code(infinite_loop_code, timeout_seconds=1.0)
    assert res.status == ExecutionStatus.TIMEOUT


def test_api_practice_execute_run():
    """Verify the /api/practice/execute endpoint in run mode."""
    client = TestClient(app)
    c_code = """#include <stdio.h>
int main() {
    printf("Result: 100\\n");
    return 0;
}
"""
    res = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Pointers",
        "source_code": c_code,
        "is_submission": False,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "Result: 100" in data["stdout"]
    assert data["passed"] is None


def test_api_practice_execute_submission_pass_and_fail():
    """Verify the /api/practice/execute endpoint in submission mode with expected output check."""
    client = TestClient(app)
    c_code = """#include <stdio.h>
int main() {
    printf("10 20\\n");
    return 0;
}
"""
    # 1. Matching expected output -> passed
    res_pass = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Pointers",
        "source_code": c_code,
        "expected_output": "10 20",
        "is_submission": True,
    })
    assert res_pass.status_code == 200
    assert res_pass.json()["passed"] is True

    # 2. Non-matching expected output -> failed
    res_fail = client.post("/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Pointers",
        "source_code": c_code,
        "expected_output": "99 99",
        "is_submission": True,
    })
    assert res_fail.status_code == 200
    assert res_fail.json()["passed"] is False


def test_api_practice_generate_personalization(monkeypatch):
    """Verify that /api/practice/generate returns real student personalization values."""
    mock_challenge_text = """### Title: Dynamic Array Sum
### Problem Statement:
Calculate the sum of elements using pointer arithmetic.
- **Input Format**: Array of integers
- **Output Format**: Single integer sum
- **Constraints**: Use pointers only
- **Sample Input**: 1 2 3
- **Sample Output**: 6
- **Explanation**: 1 + 2 + 3 = 6

### Starter Code:
```c
#include <stdio.h>
int main() {
    int a[3] = {1, 2, 3};
    int *p = a;
    int sum = *p + *(p+1) + *(p+2);
    printf("%d\\n", sum);
    return 0;
}
```

### Expected Output:
6

### Hint Ladder:
- **Hint 1 (Conceptual Guidance)**: Use pointer dereferencing.
- **Hint 2 (Approach)**: Traverse with pointer addition.
- **Hint 3 (Algorithmic Guidance)**: Accumulate values into sum.
- **Hint 4 (Implementation / Pseudocode)**: sum += *(p + i).
"""

    from eduadapt.teaching.generator import PersonalizedContentGenerator

    monkeypatch.setattr(
        PersonalizedContentGenerator,
        "generate_practice_problems",
        lambda self, topic, student_profile, learning_state: GenerationResult(
            content=mock_challenge_text,
            model_name="mistral:7b",
        ),
    )

    client = TestClient(app)

    # S001 (Advanced learner)
    res_s001 = client.post("/api/practice/generate", json={
        "student_id": "S001",
        "topic": "Pointers",
    })
    assert res_s001.status_code == 200
    data_s001 = res_s001.json()
    assert data_s001["student_id"] == "S001"
    assert data_s001["target_mastery"] == "1.00"
    assert data_s001["recommended_difficulty"] == "Advanced"
    assert "challenge" in data_s001
    assert data_s001["challenge"]["title"] == "Dynamic Array Sum"
    assert "#include <stdio.h>" in data_s001["challenge"]["starter_code"]
    assert len(data_s001["challenge"]["hints"]) == 4

    # S005 (Beginner learner)
    res_s005 = client.post("/api/practice/generate", json={
        "student_id": "S005",
        "topic": "Loops",
    })
    assert res_s005.status_code == 200
    data_s005 = res_s005.json()
    assert data_s005["student_id"] == "S005"
    assert data_s005["target_mastery"] == "0.25"
    assert data_s005["recommended_difficulty"] == "Easy"
    assert "challenge" in data_s005
