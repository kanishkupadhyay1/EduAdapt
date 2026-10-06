"""Integrated Demonstration Script for EduAdapt.

Demonstrates the single, non-agentic Generative AI pipeline:
Student ID + Target PPS Topic
        ↓
Learning Twin Adapter (Member 3)
        ↓
StudentProfile
        ↓
PPS RAG retrieval (Member 2)
        ↓
Curriculum-grounded context
        ↓
Personalized prompt
        ↓
Mistral 7B / Ollama (Member 1) or Mock LLM
        ↓
Personalized teaching content
        ↓
Basic verification
        ↓
Structured demonstration result
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

# Ensure repository root and src are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from eduadapt.adapters.student_twin_adapter import LearningTwinAdapter
from eduadapt.evaluation.c_executor import extract_c_code
from eduadapt.evaluation.regression import check_while_loop_explanation
from eduadapt.inference.base import BaseLLMClient, MockLLMClient
from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.teaching.generator import PersonalizedContentGenerator
from member3.student_state import get_student_state


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run EduAdapt Integrated End-to-End Demonstration."
    )
    parser.add_argument(
        "--student-id",
        type=str,
        default="S001",
        help="Student ID to evaluate (default: S001).",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Pointers",
        help="Target PPS curriculum topic (default: Pointers).",
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "mock"],
        default="ollama",
        help="LLM inference provider: 'ollama' or 'mock' (default: ollama).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistral:7b",
        help="Model name for Ollama inference (default: mistral:7b).",
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of PPS curriculum chunks to retrieve (default: 3).",
    )
    return parser.parse_args()


def run_demo(
    student_id: str = "S001",
    topic: str = "Pointers",
    provider: str = "ollama",
    model: str = "mistral:7b",
    ollama_url: str = "http://localhost:11434",
    top_k: int = 3,
):
    print("=" * 80)
    print("               EDUADAPT END-TO-END INTEGRATED DEMONSTRATION")
    print("=" * 80)

    # 1. Obtain raw Learning Twin state & canonical StudentProfile
    adapter = LearningTwinAdapter(default_topic=topic)
    profile = adapter.get_profile(student_id=student_id, topic=topic)
    if profile is None:
        raise ValueError(f"Student ID '{student_id}' not found in Learning Twin.")

    raw_state = get_student_state(student_id) or {}

    # Print STUDENT section
    print("\n[STUDENT]")
    print(f"- ID                     : {student_id}")
    print(f"- Mastery                : {raw_state.get('mastery', profile.mastery_levels.get(topic, 0.0)):.2f}")
    print(f"- Accuracy               : {raw_state.get('accuracy', 0.0):.2f}")
    print(f"- Learning Pace          : {raw_state.get('learning_pace', profile.preferred_pace)}")
    print(f"- Recommended Difficulty : {raw_state.get('recommended_difficulty', 'N/A')}")
    print(f"- Predicted Mastery Level: {raw_state.get('predicted_mastery_level', 'N/A')}")

    # 2. PPS Curriculum RAG Retrieval
    rag = PPSCurriculumRAG.from_defaults()
    retrieved_docs = []
    rag_context = None
    try:
        if rag is not None:
            rag_context = rag.retrieve(query=topic, top_k=top_k)
            retrieved_docs = rag_context.documents

        # Print CURRICULUM section
        print("\n[CURRICULUM]")
        print(f"- Target Topic           : {topic}")
        print(f"- Retrieved Chunks Count : {len(retrieved_docs)}")
        for idx, doc in enumerate(retrieved_docs, start=1):
            score_str = f" (score: {doc.score:.4f})" if doc.score is not None else ""
            print(f"  * Chunk {idx}: {doc.source} | Page: {doc.page} | Module: {doc.module} | Topic: {doc.topic}{score_str}")

        # 3. LLM Client & Content Generation
        llm_client: BaseLLMClient
        if provider == "ollama":
            llm_client = OllamaLLMClient(
                base_url=ollama_url,
                model_name=model,
                temperature=0.7,
                max_tokens=1024,
                timeout=180.0,
            )
        else:
            llm_client = MockLLMClient(model_name=model or "mock-pps-model")

        generator = PersonalizedContentGenerator(llm_client=llm_client, rag=rag)
        gen_result = generator.generate_for_student(topic=topic, student_profile=profile)

    finally:
        if rag is not None:
            rag.close()

    content = gen_result.content

    # 4. Print GENERATED CONTENT section
    latency = gen_result.metadata.get("latency_seconds")
    latency_str = f"{latency:.2f}s" if isinstance(latency, (int, float)) else "N/A"

    print("\n[GENERATED CONTENT]")
    print(f"- LLM Provider           : {provider} ({gen_result.model_name})")
    print(f"- Completion Tokens      : {gen_result.completion_tokens or 'N/A'}")
    print(f"- Latency                : {latency_str}")
    print("\n--- Content Text ---")
    print(content.strip())
    print("--- End Content ---\n")

    # 5. Basic Verification
    extracted_code = extract_c_code(content)
    regression_check = check_while_loop_explanation(content)

    print("[VERIFICATION]")
    print(f"- Curriculum Context     : {'Available (' + str(len(retrieved_docs)) + ' chunks retrieved)' if retrieved_docs else 'None'}")
    print(f"- Generation Completed   : {'Yes' if bool(content.strip()) else 'No'}")
    print(f"- Extracted C Code Block : {'Present (' + str(len(extracted_code.splitlines())) + ' lines)' if extracted_code else 'No markdown C code block'}")
    print(f"- Safety / Host Sandbox  : Enforced (LLM code NOT executed on host machine)")
    print(f"- Regression Check       : {'Passed' if regression_check.passed else 'Failed: ' + regression_check.explanation}")
    print("=" * 80)
    print("Integrated Demonstration run successfully completed.")
    print("=" * 80)


def main():
    args = parse_args()
    run_demo(
        student_id=args.student_id,
        topic=args.topic,
        provider=args.provider,
        model=args.model,
        ollama_url=args.ollama_url,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
