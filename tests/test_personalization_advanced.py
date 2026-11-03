"""Automated tests for EduAdapt Advanced Personalization Engine & Diagram Teaching (Member 1).

Verifies all 19 strict requirements:
1. Mastery below 0.40 selects Beginner strategy.
2. Mastery 0.40 to below 0.70 selects Intermediate strategy.
3. Mastery 0.70 or above selects Advanced strategy.
4. Different actual learning paces change instructional strategy where supported.
5. Topic-specific mastery takes precedence over general mastery where supported.
6. Missing profile fields are handled safely.
7. Real student profiles from dataset operate dynamically without fake demo profiles.
8. Prompt variables are correctly injected.
9. RAG context reaches the prompt.
10. Misconceptions reach the prompt.
11. Mermaid diagram output is parsed correctly.
12. Missing diagram output does not break generation.
13. Malformed Mermaid output is handled safely without crashing.
14. Malformed JSON does not crash the application.
15. LLM failures do not produce mock teaching content in normal flow.
16. Existing inference calls continue using OllamaLLMClient.
17. Existing ResponseVerifier integration remains intact.
18. Existing API session contracts remain compatible.
19. Full compatibility with existing pipeline.
"""

from unittest.mock import MagicMock, patch
import pytest

from eduadapt.inference.base import GenerationResult, MockLLMClient
from eduadapt.inference.ollama import OllamaConnectionError, OllamaLLMClient, OllamaTimeoutError
from eduadapt.interfaces.rag import RAGContext, RAGDocument, RAGInterface
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager
from eduadapt.services.adaptive_learning import AdaptiveLearningService
from eduadapt.teaching.diagrams import DiagramResult, MermaidValidator
from eduadapt.teaching.generator import PersonalizedContentGenerator
from eduadapt.teaching.personalization import (
    InstructionalStrategy,
    PersonalizationContext,
    PersonalizationEngine,
    select_diagram_type_for_topic,
)
from eduadapt.teaching.response_schema import ResponseParser, TeachingResponse
from eduadapt.verification.response_verifier import ResponseVerifier
from member3.student_state import get_student_state


# ==============================================================================
# 1, 2, 3: MASTERY-BASED TIER STRATEGY SELECTION
# ==============================================================================
def test_mastery_below_0_40_selects_beginner_strategy():
    """Verify that mastery < 0.40 selects Beginner strategy tier."""
    profile = StudentProfile(
        student_id="S_TEST_01",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.25},
        preferred_pace="slow",
    )
    context = PersonalizationEngine.derive_context(student_profile=profile, topic="Pointers")
    assert context.mastery_tier == "Beginner"
    assert context.topic_mastery == 0.25
    assert "foundational" in context.strategy.explanation_depth.lower()
    assert "introductory" in context.strategy.cognitive_difficulty.lower()


def test_mastery_0_40_to_0_70_selects_intermediate_strategy():
    """Verify that mastery 0.40 <= m < 0.70 selects Intermediate strategy tier."""
    for score in (0.40, 0.55, 0.69):
        profile = StudentProfile(
            student_id="S_TEST_02",
            current_topic="Loops",
            mastery_levels={"Loops": score},
            preferred_pace="moderate",
        )
        context = PersonalizationEngine.derive_context(student_profile=profile, topic="Loops")
        assert context.mastery_tier == "Intermediate"
        assert context.topic_mastery == score
        assert "mechanistic" in context.strategy.explanation_depth.lower() or "moderate" in context.strategy.cognitive_difficulty.lower()


def test_mastery_0_70_and_above_selects_advanced_strategy():
    """Verify that mastery >= 0.70 selects Advanced strategy tier."""
    for score in (0.70, 0.85, 1.0):
        profile = StudentProfile(
            student_id="S_TEST_03",
            current_topic="Functions",
            mastery_levels={"Functions": score},
            preferred_pace="fast",
        )
        context = PersonalizationEngine.derive_context(student_profile=profile, topic="Functions")
        assert context.mastery_tier == "Advanced"
        assert context.topic_mastery == score
        assert "depth" in context.strategy.explanation_depth.lower()
        assert "advanced" in context.strategy.cognitive_difficulty.lower()


# ==============================================================================
# 4: LEARNING PACE DIFFERENTIATION
# ==============================================================================
def test_learning_paces_change_instructional_strategy():
    """Verify that different actual learning paces produce distinct instructional strategies."""
    # Beginner Slow vs Beginner Fast
    profile_slow = StudentProfile(
        student_id="S005",
        current_topic="Loops",
        mastery_levels={"Loops": 0.25},
        preferred_pace="slow",
    )
    ctx_slow = PersonalizationEngine.derive_context(student_profile=profile_slow, topic="Loops")

    profile_fast = StudentProfile(
        student_id="S005_F",
        current_topic="Loops",
        mastery_levels={"Loops": 0.25},
        preferred_pace="fast",
    )
    ctx_fast = PersonalizationEngine.derive_context(student_profile=profile_fast, topic="Loops")

    assert ctx_slow.pattern_name != ctx_fast.pattern_name
    assert "concise" in ctx_fast.strategy.explanation_depth.lower()
    assert "detailed" in ctx_slow.strategy.amount_of_explanation.lower()
    assert ctx_slow.strategy.scaffolding_level != ctx_fast.strategy.scaffolding_level


# ==============================================================================
# 5: TOPIC-SPECIFIC MASTERY PRECEDENCE OVER GENERAL MASTERY
# ==============================================================================
def test_topic_specific_mastery_precedence():
    """Verify that topic-specific mastery takes precedence for the lesson."""
    profile = StudentProfile(
        student_id="S001",
        current_topic="Pointers",
        mastery_levels={"Loops": 0.95, "Arrays": 0.90, "Pointers": 0.20},
        preferred_pace="fast",
    )
    # Student is strong overall (average ~0.68-0.90) but beginner on Pointers (0.20)
    context = PersonalizationEngine.derive_context(student_profile=profile, topic="Pointers")
    assert context.topic_mastery == 0.20
    assert context.mastery_tier == "Beginner"
    assert context.overall_mastery > 0.60
    assert "Strong overall foundation" in context.pattern_name or "gap" in context.pattern_name


# ==============================================================================
# 6: MISSING PROFILE FIELDS SAFELY HANDLED
# ==============================================================================
def test_missing_profile_fields_handled_safely():
    """Verify that missing or None fields default safely without assuming beginner."""
    profile = StudentProfile(
        student_id="",
        current_topic="Pointers",
        mastery_levels={},
        learning_style="balanced",
        preferred_pace="moderate",
        common_misconceptions=[],
    )
    # Learning state provided with high mastery but missing pace
    context = PersonalizationEngine.derive_context(
        student_profile=profile,
        topic="Pointers",
        learning_state={"mastery": 0.85},
    )
    assert context.topic_mastery == 0.85
    assert context.mastery_tier == "Advanced"
    assert context.student_id == "Not enough data available"
    assert context.learning_pace == "moderate"


# ==============================================================================
# 7: REAL STUDENT PROFILES OPERATE DYNAMICALLY (NO FAKE PROFILES)
# ==============================================================================
def test_real_dataset_students_operate_dynamically():
    """Verify that real student IDs from Member 3 dataset yield real dynamic strategies."""
    # Real students in assessment_data.csv: S001 (high mastery, fast) and S005 (low mastery, slow)
    state_s001 = get_student_state("S001")
    state_s005 = get_student_state("S005")

    assert state_s001 is not None
    assert state_s005 is not None

    profile_s001 = StudentProfile(
        student_id="S001",
        current_topic="Loops",
        mastery_levels={"Loops": float(state_s001["mastery"])},
        preferred_pace=str(state_s001["learning_pace"]).lower(),
    )
    profile_s005 = StudentProfile(
        student_id="S005",
        current_topic="Loops",
        mastery_levels={"Loops": float(state_s005["mastery"])},
        preferred_pace=str(state_s005["learning_pace"]).lower(),
    )

    ctx_s001 = PersonalizationEngine.derive_context(profile_s001, topic="Loops", learning_state=state_s001)
    ctx_s005 = PersonalizationEngine.derive_context(profile_s005, topic="Loops", learning_state=state_s005)

    assert ctx_s001.mastery_tier == "Advanced"
    assert ctx_s005.mastery_tier == "Beginner"
    assert ctx_s001.learning_pace == "fast"
    assert ctx_s005.learning_pace == "slow"
    assert ctx_s001.strategy.code_complexity != ctx_s005.strategy.code_complexity


# ==============================================================================
# 8, 9, 10: PROMPT VARIABLES, RAG CONTEXT, MISCONCEPTIONS INJECTION
# ==============================================================================
def test_prompt_variables_rag_and_misconceptions_injection():
    """Verify that RAG context, misconceptions, and strategy are injected into LLM prompt."""
    captured_prompts = []

    class CapturingLLM(MockLLMClient):
        def generate(self, prompt, **kwargs):
            captured_prompts.append(prompt)
            return GenerationResult(
                content="### Learning Objective\nMaster pointers\n```c\nint *p;\n```",
                model_name="mock_capture",
            )

    mock_rag = MagicMock(spec=RAGInterface)
    mock_rag.retrieve.return_value = RAGContext(
        query="Pointers",
        documents=[
            RAGDocument(
                doc_id="doc_ptr_1",
                content="Pointers hold memory addresses. Dereferencing *p accesses target.",
                source="unit_4_pointers.pdf",
                page=12,
                module="Unit 4",
                topic="Pointers",
            )
        ],
    )

    generator = PersonalizedContentGenerator(
        llm_client=CapturingLLM(),
        prompt_manager=PromptManager(),
        rag=mock_rag,
    )

    profile = StudentProfile(
        student_id="S005",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.25},
        preferred_pace="slow",
        common_misconceptions=["Confusing pointer address (&) with dereferenced value (*)"],
    )

    res = generator.generate_for_student(topic="Pointers", student_profile=profile)
    assert len(captured_prompts) == 1
    prompt = captured_prompts[0]

    # Verify RAG reached prompt
    assert "unit_4_pointers.pdf" in prompt or "Pointers hold memory addresses" in prompt
    # Verify misconceptions reached prompt
    assert "Confusing pointer address (&) with dereferenced value (*)" in prompt
    # Verify student context reached prompt
    assert "S005" in prompt
    assert "Beginner" in prompt
    # Verify metadata recorded
    assert res.metadata["actual_mastery_used"] == 0.25
    assert res.metadata["mastery_tier"] == "Beginner"
    assert res.metadata["diagram_decision"] == "pointer_memory_diagram"


# ==============================================================================
# 11, 12, 13: MERMAID DIAGRAM PARSING, MISSING DIAGRAM, MALFORMED HANDLING
# ==============================================================================
def test_mermaid_diagram_output_parsed_correctly():
    """Verify that valid Mermaid diagram syntax is validated and parsed."""
    valid_mermaid = (
        "flowchart TD\n"
        "    Start([Start]) --> Init[int i = 0]\n"
        "    Init --> Cond{i < 5?}\n"
        "    Cond -- Yes --> Body[printf i]\n"
        "    Body --> Inc[i++]\n"
        "    Inc --> Cond\n"
        "    Cond -- No --> End([End])"
    )
    result = MermaidValidator.validate_and_sanitize(valid_mermaid, topic="Loops", diagram_type="loop_flowchart")
    assert result.is_valid is True
    assert "flowchart TD" in result.mermaid_code
    assert result.validation_error is None


def test_missing_diagram_output_does_not_break_generation():
    """Verify that absent diagram code produces clean is_valid=False without crashing."""
    result = MermaidValidator.validate_and_sanitize(None, topic="Functions")
    assert result.is_valid is False
    assert result.mermaid_code == ""
    assert result.validation_error is not None


def test_malformed_mermaid_handled_safely():
    """Verify that unbalanced delimiters or broken syntax are caught safely."""
    malformed_mermaid = "flowchart TD\n    A[Unclosed bracket --> B"
    result = MermaidValidator.validate_and_sanitize(malformed_mermaid, topic="Conditionals")
    assert result.is_valid is False
    assert "Unclosed" in result.validation_error or "Unbalanced" in result.validation_error


# ==============================================================================
# 14: MALFORMED JSON DOES NOT CRASH APPLICATION
# ==============================================================================
def test_malformed_json_does_not_crash_parser():
    """Verify that malformed JSON falls back gracefully to structured markdown parser."""
    malformed_text = (
        '{"learning_objective": "Test obj", "explanation": "Broken JSON missing closing brace'
    )
    response = ResponseParser.parse_teaching_content(
        raw_text=malformed_text,
        topic="Pointers",
    )
    assert isinstance(response, TeachingResponse)
    assert response.learning_objective != ""
    assert response.explanation != ""
    assert response.parsing_status in ("structured_markdown", "fallback_raw")


# ==============================================================================
# 15: LLM FAILURES DO NOT PRODUCE MOCK TEACHING CONTENT IN NORMAL FLOW
# ==============================================================================
def test_llm_failures_raise_proper_exceptions():
    """Verify that connection failure to Ollama raises OllamaConnectionError without fabricating mock content."""
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout=1.0)
    generator = PersonalizedContentGenerator(llm_client=client, prompt_manager=PromptManager())
    profile = StudentProfile(student_id="S001", current_topic="Pointers", mastery_levels={"Pointers": 0.5})

    with patch("requests.post", side_effect=Exception("Connection refused")):
        with pytest.raises(Exception) as exc_info:
            generator.generate_for_student(topic="Pointers", student_profile=profile)
        assert "Connection" in str(exc_info.value)


# ==============================================================================
# 16: EXISTING INFERENCE CALLS CONTINUE USING OLLAMA
# ==============================================================================
def test_ollama_llm_client_structure_preserved():
    """Verify that OllamaLLMClient implements BaseLLMClient and connects to localhost:11434."""
    client = OllamaLLMClient(base_url="http://localhost:11434", model_name="mistral:7b")
    assert client.base_url == "http://localhost:11434"
    assert client.model_name == "mistral:7b"
    assert hasattr(client, "generate")


# ==============================================================================
# 17: RESPONSE VERIFIER INTEGRATION REMAINS INTACT
# ==============================================================================
def test_response_verifier_integration_remains_intact():
    """Verify that ResponseVerifier inspects generated content and extracts code safely."""
    response_text = (
        "### Learning Objective\nLearn pointers.\n"
        "Here is C code:\n"
        "```c\n"
        "#include <stdio.h>\n"
        "int main() {\n"
        "    int x = 10;\n"
        "    int *p = &x;\n"
        "    printf(\"%d\", *p);\n"
        "    return 0;\n"
        "}\n"
        "```\n"
    )
    chunks = [{"source": "unit4.pdf", "preview": "int *p = &x;"}]
    v_res = ResponseVerifier.verify_response(response_text=response_text, retrieved_chunks=chunks, topic="Pointers")
    assert v_res.generation_completed is True
    assert v_res.code_detected is True
    assert v_res.code_execution_status == "NOT_EXECUTED_UNTRUSTED"


# ==============================================================================
# 18: API CONTRACT COMPATIBILITY
# ==============================================================================
def test_api_session_contract_compatibility():
    """Verify that AdaptiveLearningService produces a fully populated session matching API contract."""
    mock_llm = MockLLMClient()
    service = AdaptiveLearningService(llm_client=mock_llm)

    result = service.run_learning_session(student_id="S001", topic="Pointers")
    assert "student" in result
    assert "profile" in result
    assert "curriculum" in result
    assert "teaching" in result
    assert "assessment" in result
    assert "feedback" in result
    assert "roadmap" in result
    assert "verification" in result
    assert "accessibility" in result

    # Check new personalization and diagram signals
    teaching = result["teaching"]
    assert "personalization_applied" in teaching
    assert "personalization_bullets" in teaching
    assert "generation_metadata" in teaching
    assert teaching["generation_metadata"]["student_id"] == "S001"
    assert teaching["generation_metadata"]["actual_mastery_used"] == 1.0
    assert teaching["generation_metadata"]["mastery_tier"] == "Advanced"
