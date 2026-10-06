"""Smoke tests for EduAdapt Generative AI Module.

Verifies basic project integrity, configuration, prompt management,
inference mock pipeline, and interface data contracts.
"""

import json
from pathlib import Path
from eduadapt.config import Settings, get_settings
from eduadapt.main import build_app, main
from eduadapt.inference.base import MockLLMClient
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.generator import PersonalizedContentGenerator
from eduadapt.feedback.evaluator import FeedbackGenerator
from eduadapt.roadmap.planner import RoadmapGenerator
from eduadapt.interfaces.rag import RAGContext
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.training.pipeline import TrainingPipelineStub


def test_settings_initialization():
    """Verify that settings can be instantiated with defaults."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "EduAdapt Generative AI Module"
    assert settings.llm_provider == "mock"


def test_main_app_wiring():
    """Verify application factory and components initialization."""
    components = build_app()
    assert "settings" in components
    assert "llm_client" in components
    assert "prompt_manager" in components
    assert "teaching_service" in components
    assert "feedback_service" in components
    assert "roadmap_service" in components

    exit_code = main()
    assert exit_code == 0


def test_mock_inference_and_teaching():
    """Verify teaching generation using mock LLM client."""
    client = MockLLMClient()
    pm = PromptManager()
    teaching = PersonalizedContentGenerator(llm_client=client, prompt_manager=pm)

    result = teaching.generate_explanation(
        topic="Pointers",
        learning_preference="visual",
        context="Introductory lesson",
    )
    assert result.content.startswith("[Mock LLM Output")
    assert result.model_name == "mock-pps-model"
    assert result.prompt_tokens is not None and result.prompt_tokens > 0

    # Verify generate_for_student with mock RAG interface
    from eduadapt.interfaces.rag import RAGInterface, RAGDocument
    class DummyRAG(RAGInterface):
        def retrieve(self, query: str, top_k: int = 3) -> RAGContext:
            return RAGContext(
                query=query,
                documents=[
                    RAGDocument(doc_id="1", content="Pointer chunk", source="unit2.pptx", page=1)
                ],
            )

    teaching_rag = PersonalizedContentGenerator(llm_client=client, prompt_manager=pm, rag=DummyRAG())
    profile = StudentProfile(
        student_id="S001",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.8},
        preferred_pace="fast",
    )
    student_res = teaching_rag.generate_for_student(topic="Pointers", student_profile=profile)
    assert student_res.content.startswith("[Mock LLM Output")


def test_feedback_generation():
    """Verify feedback generator using mock LLM client."""
    client = MockLLMClient()
    pm = PromptManager()
    feedback = FeedbackGenerator(llm_client=client, prompt_manager=pm)

    result = feedback.generate_feedback(
        problem_description="Swap two numbers using pointers",
        student_code="void swap(int a, int b) { int t = a; a = b; b = t; }",
    )
    assert result.content.startswith("[Mock LLM Output")


def test_roadmap_generation():
    """Verify roadmap generator using mock LLM client."""
    client = MockLLMClient()
    pm = PromptManager()
    roadmap = RoadmapGenerator(llm_client=client, prompt_manager=pm)

    result = roadmap.generate_roadmap(
        target_competency="Pointers and Dynamic Memory",
        current_mastery="Beginner",
    )
    assert result.content.startswith("[Mock LLM Output")


def test_training_pipeline_stub():
    """Verify training stub executes safely without invoking any actual training."""
    stub = TrainingPipelineStub()
    train_status = stub.run_training_stub()
    assert train_status["status"] == "ready"
    eval_status = stub.evaluate_stub()
    assert eval_status["status"] == "ready"


def test_interfaces_and_mock_data():
    """Verify mock data files conform to interface Pydantic models."""
    root_dir = Path(__file__).resolve().parent.parent

    # Test Student Profile
    student_file = root_dir / "data" / "mock" / "sample_student.json"
    assert student_file.exists()
    with open(student_file, "r", encoding="utf-8") as f:
        student_data = json.load(f)
    profile = StudentProfile(**student_data)
    assert profile.student_id == "std_1001"
    assert "Pointers and Memory" in profile.mastery_levels

    # Test RAG Context
    rag_file = root_dir / "data" / "mock" / "sample_rag_context.json"
    assert rag_file.exists()
    with open(rag_file, "r", encoding="utf-8") as f:
        rag_data = json.load(f)
    context = RAGContext(**rag_data)
    assert len(context.documents) == 1
    assert "memory address" in context.to_context_str()
