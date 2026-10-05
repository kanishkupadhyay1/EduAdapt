"""Unit tests for the PPS Teaching Evaluation Framework.

Tests benchmark dataset validity, C compiler discovery, trusted reference compilation and execution,
execution timeout handling, LLM untrusted code isolation, while-loop regression detection,
concept-coverage indicators, and evaluation serialization.
"""

import json
from pathlib import Path
import tempfile
import pytest

from eduadapt.evaluation.benchmark import load_benchmark, validate_benchmark
from eduadapt.evaluation.c_executor import (
    CExecutor,
    discover_c_compiler,
    extract_c_code,
)
from eduadapt.evaluation.models import (
    BenchmarkItem,
    CodeExecutionResult,
    EvaluationRunSummary,
    ExecutionStatus,
    ManualReviewRating,
    StudentProfileContext,
)
from eduadapt.evaluation.regression import check_while_loop_explanation
from eduadapt.evaluation.runner import PPSEvaluationRunner, compute_concept_coverage
from eduadapt.inference.base import MockLLMClient


def test_benchmark_dataset_integrity():
    """Verify that the benchmark dataset loads, contains 20 items, and conforms to all schema rules."""
    items = load_benchmark()
    assert len(items) == 20
    validate_benchmark(items, require_full_curriculum=True)

    expected_topics = {
        "Variables and data types",
        "Operators and expressions",
        "Conditionals",
        "For and while loops",
        "Nested loops",
        "Arrays",
        "Functions",
    }
    actual_topics = {item.topic for item in items}
    assert actual_topics == expected_topics

    for item in items:
        assert item.id.startswith("pps_")
        assert item.difficulty in ("Beginner", "Intermediate", "Advanced")
        assert 0.0 <= item.student_mastery_level <= 1.0
        assert len(item.expected_key_concepts) > 0
        assert len(item.concept_coverage_keywords) > 0
        assert len(item.reference_answer) > 20
        assert item.student_profile.student_id is not None
        assert item.student_profile.preferred_response_format != ""


def test_compiler_discovery():
    """Verify that compiler discovery finds gcc at C:\\MinGW\\bin\\gcc.exe or handles missing gracefully."""
    compiler = discover_c_compiler()
    # On this machine, GCC exists in MinGW
    if compiler:
        assert Path(compiler).is_file()
        assert "gcc" in compiler.lower()

    # Verify fallback for non-existent path
    assert discover_c_compiler("/non/existent/path/compiler_xyz") is not None or discover_c_compiler("/non/existent/path/compiler_xyz") is None


def test_trusted_reference_execution_success():
    """Verify that trusted reference C code compiles and produces expected output."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered on host.")

    valid_c_code = (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        '    printf("Hello PPS Evaluation\\n");\n'
        "    return 0;\n"
        "}\n"
    )

    result = executor.execute_trusted_reference(valid_c_code)
    assert result.status == ExecutionStatus.SUCCESS
    assert result.is_trusted_reference is True
    assert result.exit_code == 0
    assert "Hello PPS Evaluation" in result.stdout
    assert result.execution_time_seconds >= 0.0


def test_trusted_reference_execution_compilation_error():
    """Verify that malformed trusted C code returns COMPILATION_ERROR status without crashing."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered on host.")

    broken_c_code = (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    syntax_error_here;\n"
        "    return 0;\n"
        "}\n"
    )

    result = executor.execute_trusted_reference(broken_c_code)
    assert result.status == ExecutionStatus.COMPILATION_ERROR
    assert result.exit_code != 0
    assert len(result.compiler_output) > 0


def test_trusted_reference_timeout_handling():
    """Verify that infinite loops in trusted C code trigger TIMEOUT status and terminate cleanly."""
    executor = CExecutor(default_timeout_seconds=1.0)
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered on host.")

    infinite_loop_code = (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    volatile int x = 0;\n"
        "    while (1) { x++; }\n"
        "    return 0;\n"
        "}\n"
    )

    result = executor.execute_trusted_reference(infinite_loop_code, timeout_seconds=1.0)
    assert result.status == ExecutionStatus.TIMEOUT
    assert "timed out" in result.notes.lower()


def test_untrusted_llm_code_safety_invariant():
    """Verify safety invariant: LLM code is NEVER executed, extracted, and marked NOT_EXECUTED_UNTRUSTED."""
    executor = CExecutor()
    llm_output = (
        "Here is the solution in C:\n"
        "```c\n"
        "#include <stdio.h>\n"
        "int main() {\n"
        '    printf("Untrusted code\\n");\n'
        "    return 0;\n"
        "}\n"
        "```\n"
        "This runs fine."
    )

    result = executor.handle_untrusted_llm_code(llm_output)
    assert result.status == ExecutionStatus.NOT_EXECUTED_UNTRUSTED
    assert result.is_trusted_reference is False
    assert "printf" in result.source_code
    assert result.stdout == ""  # Never executed!
    assert result.exit_code is None


def test_code_block_extraction():
    """Verify accurate extraction of C code blocks from markdown responses."""
    text_with_c = "Intro text\n```c\nint a = 10;\n```\nExplanation."
    assert extract_c_code(text_with_c) == "int a = 10;"

    text_uppercase = "```C\nint b = 20;\n```"
    assert extract_c_code(text_uppercase) == "int b = 20;"

    text_no_code = "Just plain textual explanation."
    assert extract_c_code(text_no_code) is None


def test_while_loop_regression_detector_on_known_error():
    """Verify that the targeted while-loop detector flags the known Mistral 7B error."""
    # Erroneous output from Scenario 4
    erroneous_text = (
        "Explanation: This example demonstrates calculating the sum of the first N natural numbers "
        "using a while loop. The loop continues until `i` is greater than `n+1`, which ensures that "
        "every natural number up to `n` is included in the sum calculation."
    )

    check = check_while_loop_explanation(erroneous_text)
    assert check.checked is True
    assert check.passed is False
    assert check.detected_error_phrase is not None
    assert "greater than `n+1`" in check.detected_error_phrase.lower()


def test_while_loop_regression_detector_on_correct_explanation():
    """Verify that the targeted while-loop detector passes a correct explanation."""
    correct_text = (
        "In `while (i <= n)`, the loop condition checks if i <= n before every iteration. "
        "The loop terminates when i reaches n+1 because i <= n evaluates to false. "
        "Therefore, the final value of i is n+1."
    )

    check = check_while_loop_explanation(correct_text)
    assert check.checked is True
    assert check.passed is True
    assert check.detected_error_phrase is None
    assert "terminates when i reaches n+1" in check.explanation


def test_concept_coverage_indicator():
    """Verify concept-coverage keyword matching indicator."""
    keywords = ["int", "float", "sizeof", "memory", "undefined behavior"]
    text = "In C, an int is an integer type. Use sizeof to determine memory requirements."

    indicator = compute_concept_coverage(text, keywords)
    assert indicator.total_keywords == 5
    assert set(indicator.matched_keywords) == {"int", "sizeof", "memory"}
    assert set(indicator.missing_keywords) == {"float", "undefined behavior"}
    assert indicator.coverage_ratio == 0.6


def test_evaluation_runner_end_to_end_with_mock():
    """Verify the entire evaluation pipeline using MockLLMClient and a 2-question subset."""
    items = load_benchmark()
    test_subset = items[:2]  # pps_01 and pps_02

    mock_client = MockLLMClient(model_name="mock-pps-model")
    runner = PPSEvaluationRunner(llm_client=mock_client)

    summary = runner.run_benchmark(benchmark_items=test_subset)

    assert isinstance(summary, EvaluationRunSummary)
    assert summary.total_questions == 2
    assert summary.successful_inferences == 2
    assert len(summary.results) == 2
    assert summary.model_name == "mock-pps-model"

    for res in summary.results:
        assert res.benchmark_id in ("pps_01", "pps_02")
        assert res.generated_content.startswith("[Mock LLM Output")
        assert res.automated_indicators.llm_code_execution_status in (
            ExecutionStatus.NOT_EXECUTED_UNTRUSTED,
            ExecutionStatus.NO_CODE,
        )
        # Trusted reference check
        if res.automated_indicators.trusted_reference_execution:
            assert res.automated_indicators.trusted_reference_execution.is_trusted_reference is True
        # Manual review placeholder check
        assert res.manual_review.is_reviewed is False
        assert res.manual_review.conceptual_correctness is None


def test_evaluation_results_serialization(tmp_path):
    """Verify that evaluation results serialize to JSON and reload cleanly."""
    items = load_benchmark()
    test_subset = [items[0]]

    mock_client = MockLLMClient(model_name="mock-pps-model")
    runner = PPSEvaluationRunner(llm_client=mock_client)

    summary = runner.run_benchmark(benchmark_items=test_subset)

    out_file = tmp_path / "test_eval_output.json"
    runner.save_results(summary, out_file)

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_questions"] == 1
    assert data["results"][0]["benchmark_id"] == "pps_01"
    assert data["results"][0]["manual_review"]["is_reviewed"] is False
