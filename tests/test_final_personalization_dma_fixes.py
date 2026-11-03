"""Final verification and regression tests for EduAdapt Personalization, Diagram Quality, and C Sandbox.

Covers:
1. Student-specific personalization across Beginner, Intermediate, Advanced, and Pacing.
2. Complete educational lessons with valid C implementations for all 10 PPS topics.
3. Accurate, valid Mermaid diagrams with multi-diagram handling.
4. C Sandbox execution with standard input (stdin), compiler diagnostics, and output comparison.
5. Strict topic specificity with zero leakage across curriculum topics.
"""

import pytest
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.services.question_service import PPS_CURRICULUM_SEQUENCE
from eduadapt.teaching.diagrams import get_topic_default_mermaid, MermaidValidator
from eduadapt.teaching.personalization import PersonalizationEngine
from eduadapt.teaching.response_schema import (
    ResponseParser,
    extract_c_code,
    normalize_topic_name,
    _get_defaults_for_topic,
    _get_challenge_defaults,
)


def test_personalization_changes_teaching_by_tier():
    """Ensure Beginner, Intermediate, and Advanced tiers produce distinctly different lessons."""
    topic = "Pointers"
    beg_lesson = ResponseParser.parse_teaching_content("", topic=topic, mastery_tier="Beginner")
    inter_lesson = ResponseParser.parse_teaching_content("", topic=topic, mastery_tier="Intermediate")
    adv_lesson = ResponseParser.parse_teaching_content("", topic=topic, mastery_tier="Advanced")

    # Content must not be identical
    assert beg_lesson.explanation != inter_lesson.explanation
    assert inter_lesson.explanation != adv_lesson.explanation
    assert beg_lesson.c_code != inter_lesson.c_code
    assert inter_lesson.c_code != adv_lesson.c_code
    assert beg_lesson.learning_objective != adv_lesson.learning_objective

    # Beginner must emphasize fundamentals and memory address &
    assert "&num" in beg_lesson.c_code or "num = 10" in beg_lesson.c_code
    # Intermediate must demonstrate functions/arrays with pointers
    assert "swap" in inter_lesson.c_code or "arr" in inter_lesson.c_code
    # Advanced must demonstrate double indirection or memory management
    assert "**" in adv_lesson.c_code or "malloc" in adv_lesson.c_code


def test_all_10_pps_topics_covered_with_c_implementations():
    """Verify that every single PPS curriculum topic has complete, runnable C code and walkthroughs."""
    for topic in PPS_CURRICULUM_SEQUENCE:
        for tier in ("Beginner", "Intermediate", "Advanced"):
            lesson = ResponseParser.parse_teaching_content("", topic=topic, mastery_tier=tier)
            assert lesson.c_code, f"Missing C code for {topic} ({tier})"
            assert "#include" in lesson.c_code, f"Missing headers in C code for {topic} ({tier})"
            assert "main" in lesson.c_code, f"Missing main function in C code for {topic} ({tier})"
            assert len(lesson.walkthrough_steps) >= 2, f"Missing walkthrough for {topic} ({tier})"
            assert len(lesson.common_mistakes) >= 2, f"Missing common mistakes for {topic} ({tier})"
            assert lesson.understanding_check.get("question"), f"Missing understanding check for {topic} ({tier})"


def test_no_pointers_leakage_in_other_topics():
    """Ensure other topics (e.g. Loops, Strings, DMA) do not leak Pointers defaults."""
    dma = _get_defaults_for_topic("Dynamic Memory Allocation", "Intermediate")
    assert "malloc" in dma["code"]
    assert "free" in dma["code"]
    assert "Pointers in C" not in dma["explanation"]

    loops = _get_defaults_for_topic("Loops", "Beginner")
    assert "for" in loops["code"] or "while" in loops["code"]
    assert "pointer" not in loops["objective"].lower()

    strings = _get_defaults_for_topic("Strings", "Beginner")
    assert "greeting" in strings["code"] or "string" in strings["objective"].lower()


def test_diagram_personalization_and_validity():
    """Verify diagrams change by tier and remain valid Mermaid flowchart syntax."""
    for topic in PPS_CURRICULUM_SEQUENCE:
        for tier in ("Beginner", "Intermediate", "Advanced"):
            mermaid_src = get_topic_default_mermaid(topic, mastery_tier=tier)
            assert mermaid_src.startswith("flowchart"), f"Invalid diagram header for {topic} ({tier})"
            res = MermaidValidator.validate_and_sanitize(mermaid_src, topic=topic, mastery_tier=tier)
            assert res.is_valid, f"Diagram validation failed for {topic} ({tier})"
            assert res.mermaid_code, f"Empty mermaid code for {topic} ({tier})"


def test_extract_c_code_when_mermaid_comes_first():
    """Ensure C code is correctly extracted even when a Mermaid diagram precedes it in the output."""
    raw = (
        "### Visual Architecture Diagram\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    A[\"Node A\"] --> B[\"Node B\"]\n"
        "```\n\n"
        "### C Code Implementation\n"
        "```c\n"
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    printf(\"Validated\\n\");\n"
        "    return 0;\n"
        "}\n"
        "```\n"
    )
    code = extract_c_code(raw)
    assert code is not None
    assert "printf(\"Validated\\n\");" in code
    assert "flowchart" not in code


def test_c_executor_dma_with_stdin_and_exit_code():
    """Verify that student DMA code executes with standard input and produces expected output."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("C compiler GCC is not available on host.")

    student_code = (
        "#include <stdio.h>\n"
        "#include <stdlib.h>\n\n"
        "void createArray(int *array, int size);\n"
        "void printArray(int *array, int size);\n\n"
        "int main(void) {\n"
        "    int size;\n"
        "    if (scanf(\"%d\", &size) != 1 || size <= 0) {\n"
        "        return 0;\n"
        "    }\n\n"
        "    int *array = (int *)malloc(size * sizeof(int));\n"
        "    if (array == NULL) {\n"
        "        return 1;\n"
        "    }\n\n"
        "    createArray(array, size);\n"
        "    printArray(array, size);\n\n"
        "    free(array);\n"
        "    return 0;\n"
        "}\n\n"
        "void createArray(int *array, int size) {\n"
        "    for (int i = 0; i < size; i++) {\n"
        "        scanf(\"%d\", &array[i]);\n"
        "    }\n"
        "}\n\n"
        "void printArray(int *array, int size) {\n"
        "    for (int i = 0; i < size; i++) {\n"
        "        printf(\"%d%s\", array[i], (i == size - 1) ? \"\" : \" \");\n"
        "    }\n"
        "    printf(\"\\n\");\n"
        "}\n"
    )

    # 1. Test with valid stdin: should pass and produce 10 20 30 40 50
    res = executor.execute_student_code(student_code, stdin_input="5\n10 20 30 40 50")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.exit_code == 0
    assert res.stdout.strip() == "10 20 30 40 50"

    # 2. Test with empty stdin: should return 0 safely without hanging or timeout
    res_empty = executor.execute_student_code(student_code, stdin_input="")
    assert res_empty.status == ExecutionStatus.SUCCESS
    assert res_empty.exit_code == 0


def test_personalization_engine_summary_and_rationale():
    """Verify that PersonalizationEngine produces observable summaries with pedagogical rationale."""
    profile_beg = StudentProfile(
        student_id="S_TEST_BEG",
        current_topic="Dynamic Memory Allocation",
        mastery_levels={"Dynamic Memory Allocation": 0.20},
        preferred_pace="slow",
        common_misconceptions=["Failing to check malloc NULL return", "Memory leak without free"],
    )
    ctx_beg = PersonalizationEngine.derive_context(profile_beg, "Dynamic Memory Allocation")
    assert ctx_beg.mastery_tier == "Beginner"
    assert ctx_beg.learning_pace == "slow"
    assert "rationale" in ctx_beg.personalization_summary
    assert "concept_focus" in ctx_beg.personalization_summary
    assert "Failing to check malloc" in ctx_beg.personalization_summary["concept_focus"]

    profile_adv = StudentProfile(
        student_id="S_TEST_ADV",
        current_topic="Dynamic Memory Allocation",
        mastery_levels={"Dynamic Memory Allocation": 0.85},
        preferred_pace="fast",
    )
    ctx_adv = PersonalizationEngine.derive_context(profile_adv, "Dynamic Memory Allocation")
    assert ctx_adv.mastery_tier == "Advanced"
    assert ctx_adv.learning_pace == "fast"
    assert ctx_adv.personalization_summary["rationale"] != ctx_beg.personalization_summary["rationale"]


def test_topic_coding_challenges_all_topics():
    """Verify that all 10 topics have valid, complete coding challenge contracts."""
    for topic in PPS_CURRICULUM_SEQUENCE:
        chal = _get_challenge_defaults(topic)
        assert chal["problem_statement"]
        assert chal["input_format"]
        assert chal["output_format"]
        assert chal["expected_output"]
        assert chal["starter_code"]
        assert "#include" in chal["starter_code"]
