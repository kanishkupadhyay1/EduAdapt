"""Tests for the Adaptive Learning demonstration and service layer."""

import pytest
from eduadapt.inference.base import MockLLMClient
from eduadapt.interfaces.rag import RAGContext, RAGDocument, RAGInterface
from eduadapt.services.adaptive_learning import AdaptiveLearningService


class DummyCurriculumRAG(RAGInterface):
    """Simple in-memory RAG fixture for testing."""

    def retrieve(self, query: str, top_k: int = 3) -> RAGContext:
        docs = [
            RAGDocument(
                doc_id=f"chunk_{i}",
                content=f"Curriculum context about {query} chunk {i}",
                source="unit3_pointers.pptx",
                score=0.95 - (i * 0.05),
                page=10 + i,
                module="Unit 3",
                topic=query,
            )
            for i in range(1, top_k + 1)
        ]
        return RAGContext(query=query, documents=docs)


def test_service_run_learning_session_s001():
    """Verify S001 can run through the service with all required sections."""
    mock_llm = MockLLMClient(model_name="mock-test-model")
    rag = DummyCurriculumRAG()
    service = AdaptiveLearningService(llm_client=mock_llm, rag=rag)

    result = service.run_learning_session(student_id="S001", topic="Pointers", top_k=3)

    # 1. Expected top-level keys
    expected_sections = [
        "student",
        "profile",
        "curriculum",
        "teaching",
        "assessment",
        "feedback",
        "learning_state",
        "roadmap",
        "verification",
    ]
    for section in expected_sections:
        assert section in result, f"Missing section: {section}"

    # 2. Student section validation
    student = result["student"]
    assert student["student_id"] == "S001"
    assert student["found"] is True
    assert student["mastery"] == 1.0
    assert student["accuracy"] == 1.0
    assert student["learning_pace"] == "Fast"
    assert student["recommended_difficulty"] == "Advanced"
    assert student["predicted_mastery_level"] == "High"

    # 3. Profile section validation
    profile = result["profile"]
    assert profile["current_topic"] == "Pointers"
    assert "Pointers" in profile["mastery_levels"]

    # 4. Curriculum RAG validation
    curriculum = result["curriculum"]
    assert curriculum["topic"] == "Pointers"
    assert curriculum["retrieved_count"] == 3
    assert len(curriculum["retrieved_chunks"]) == 3
    assert curriculum["retrieved_chunks"][0]["source"] == "unit3_pointers.pptx"

    # 5. Teaching validation
    teaching = result["teaching"]
    assert "generated_teaching_content" in teaching
    assert teaching["model"] == "mock-test-model"
    assert len(teaching["generated_teaching_content"]) > 0

    # 6. Assessment validation
    assessment = result["assessment"]
    assert assessment["topic"] == "Pointers"
    assert "question" in assessment
    assert assessment["score"] > 0
    assert assessment["accuracy"] == 1.0

    # 7. Feedback & Roadmap validation
    assert len(result["feedback"]["feedback"]) > 0
    assert len(result["roadmap"]["roadmap_content"]) > 0

    # 8. Learning State validation
    learning_state = result["learning_state"]
    assert learning_state["can_update_in_place"] is True
    assert "updated_state" in learning_state
    assert learning_state["updated_state"]["student_id"] == "S001"

    # 9. Verification section validation
    ver = result["verification"]
    assert ver["curriculum_context_available"] is True
    assert ver["generation_completed"] is True
    assert ver["code_execution_status"] == "NOT_EXECUTED_UNTRUSTED"
    assert "Enforced" in ver["safety_status"]


def test_service_handles_unknown_student_safely():
    """Verify unknown student (e.g. S999) is handled gracefully without crashing."""
    mock_llm = MockLLMClient()
    rag = DummyCurriculumRAG()
    service = AdaptiveLearningService(llm_client=mock_llm, rag=rag)

    result = service.run_learning_session(student_id="S999", topic="Loops")

    student = result["student"]
    assert student["student_id"] == "S999"
    assert student["found"] is False
    assert student["mastery"] == 0.0

    # Downstream generation still succeeds using fallback profile
    assert result["teaching"]["generated_teaching_content"] != ""
    assert result["verification"]["generation_completed"] is True
    assert result["learning_state"]["can_update_in_place"] is False


def test_service_without_rag():
    """Verify service runs gracefully when RAG interface is None."""
    mock_llm = MockLLMClient()
    service = AdaptiveLearningService(llm_client=mock_llm, rag=None)

    result = service.run_learning_session(student_id="S001", topic="Arrays")
    assert result["curriculum"]["retrieved_count"] == 0
    assert result["verification"]["curriculum_context_available"] is False
    assert result["verification"]["generation_completed"] is True
