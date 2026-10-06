"""Comprehensive End-to-End Demonstration Script for EduAdapt.

Demonstrates ONE complete realistic student journey:
Student: S001
Topic: Pointers

Flow:
1. INITIAL STUDENT STATE
2. PERSONALIZED PROFILE
3. CURRICULUM RETRIEVAL (Top 3 PPS PPTX sources)
4. PERSONALIZED TEACHING (Mistral 7B via Ollama or Mock)
5. PRACTICE / ASSESSMENT (Post-learning PPS assessment evaluation)
6. FEEDBACK (Personalized code feedback)
7. UPDATED LEARNING STATE (Learning Twin state recomputation)
8. PERSONALIZED ROADMAP (Curriculum-grounded milestone roadmap)
9. VERIFICATION & SAFETY (LLM code safety isolation & regression checks)
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure repository root and src are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from eduadapt.inference.base import BaseLLMClient, MockLLMClient
from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.services.adaptive_learning import AdaptiveLearningService


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run EduAdapt Adaptive Learning End-to-End Demonstration."
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
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit JSON frontend contract output only.",
    )
    return parser.parse_args()


def run_full_demo(
    student_id: str = "S001",
    topic: str = "Pointers",
    provider: str = "ollama",
    model: str = "mistral:7b",
    ollama_url: str = "http://localhost:11434",
    top_k: int = 3,
    json_output: bool = False,
):
    # Initialize LLM Client
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

    # Initialize RAG
    rag = PPSCurriculumRAG.from_defaults(allow_empty=True)

    try:
        service = AdaptiveLearningService(llm_client=llm_client, rag=rag)
        result = service.run_learning_session(
            student_id=student_id,
            topic=topic,
            top_k=top_k,
            generate_roadmap=True,
            generate_feedback=True,
        )
    finally:
        if rag is not None:
            rag.close()

    if json_output:
        print(json.dumps(result, indent=2))
        return result

    # Formatted display matching PART 6
    print("=" * 80)
    print("                 EDUADAPT ADAPTIVE LEARNING DEMO")
    print("=" * 80)

    # 1. INITIAL STUDENT STATE
    stu = result["student"]
    print("\n1. INITIAL STUDENT STATE")
    print(f"- Student ID             : {stu['student_id']}")
    print(f"- Mastery                : {stu['mastery']:.2f}")
    print(f"- Accuracy               : {stu['accuracy']:.2f}")
    print(f"- Learning Pace          : {stu['learning_pace']}")
    print(f"- Recommended Difficulty : {stu['recommended_difficulty']}")
    print(f"- Predicted Mastery      : {stu['predicted_mastery_level']}")

    # 2. PERSONALIZED PROFILE
    prof = result["profile"]
    print("\n2. PERSONALIZED PROFILE")
    print(f"- Topic                  : {prof['current_topic']}")
    print(f"- Mastery Level          : {prof['mastery_levels'].get(topic, 0.0):.2f}")
    print(f"- Preferred Pace         : {prof['preferred_pace']}")
    print(f"- Learning Style         : {prof['learning_style']}")

    # 3. CURRICULUM RETRIEVAL
    curr = result["curriculum"]
    print(f"\n3. CURRICULUM RETRIEVAL")
    print(f"Top {len(curr['retrieved_chunks'])} retrieved PPS sources for query '{curr['topic']}':")
    for idx, c in enumerate(curr["retrieved_chunks"], start=1):
        score_str = f" (score: {c['relevance_score']:.4f})" if c.get("relevance_score") is not None else ""
        print(f"  [{idx}] PPTX: {c['source']}")
        print(f"      Slide/Page: {c['slide_or_page']} | Unit: {c['unit_or_module']} | Topic: {c['topic']}{score_str}")

    # 4. PERSONALIZED TEACHING
    teach = result["teaching"]
    print("\n4. PERSONALIZED TEACHING")
    print(f"- Model / Provider       : {teach['model']} ({teach['provider']})")
    if teach.get("latency") is not None:
        print(f"- Latency                : {teach['latency']:.2f}s")
    if teach.get("token_information", {}).get("completion_tokens"):
        print(f"- Completion Tokens      : {teach['token_information']['completion_tokens']}")
    print("\n--- Generated Teaching Content ---")
    print(teach["generated_teaching_content"].strip())
    print("--- End Teaching Content ---")

    # 5. PRACTICE / ASSESSMENT
    assess = result["assessment"]
    print("\n5. PRACTICE / ASSESSMENT")
    print(f"- Assessment Topic       : {assess['topic']}")
    print(f"- Question               : {assess['question']}")
    for opt in assess["options"]:
        print(f"  {opt}")
    print(f"- Evaluation Score       : {assess['score']} / 100")
    print(f"- Accuracy               : {assess['accuracy']:.2f}")
    print(f"- Attempts               : {assess['attempts']}")
    print(f"- Time Taken             : {assess['time_taken_seconds']}s")
    print(f"- Correct Answer         : Option {assess['correct_option']} ({assess['explanation']})")

    # 6. FEEDBACK
    fb = result["feedback"]
    print("\n6. FEEDBACK")
    if fb and fb.get("feedback"):
        print(fb["feedback"].strip())
    else:
        print("No feedback generated.")

    # 7. UPDATED LEARNING STATE
    ls = result["learning_state"]
    print("\n7. UPDATED LEARNING STATE")
    if ls.get("can_update_in_place") and ls.get("updated_state"):
        up = ls["updated_state"]
        print(f"- Status                 : {ls['status_message']}")
        print(f"- Updated Mastery        : {up['mastery']:.2f}")
        print(f"- Updated Accuracy       : {up['accuracy']:.2f}")
        print(f"- Updated Pace           : {up['learning_pace']}")
        print(f"- Recommended Difficulty : {up['recommended_difficulty']}")
    else:
        print(f"- Status                 : {ls.get('status_message', 'No update available.')}")

    # 8. PERSONALIZED ROADMAP
    rm = result["roadmap"]
    print("\n8. PERSONALIZED ROADMAP")
    print(f"- Target Competency      : {rm.get('target_competency', 'PPS')}")
    print(f"- Baseline Mastery       : {rm.get('current_mastery', 'Beginner')}")
    print("\n--- Roadmap Sequence ---")
    print(rm.get("roadmap_content", "No roadmap available.").strip())
    print("--- End Roadmap Sequence ---")

    # 9. VERIFICATION
    ver = result["verification"]
    print("\n9. VERIFICATION")
    print(f"- RAG Context Grounding  : {'Available' if ver['curriculum_context_available'] else 'None'} ({ver['retrieved_chunks_count']} chunks)")
    print(f"- Generation Completed   : {'Yes' if ver['generation_completed'] else 'No'}")
    print(f"- C Code Extracted       : {'Yes (' + str(ver['extracted_code_lines']) + ' lines)' if ver['code_extracted'] else 'No'}")
    print(f"- Code Safety / Sandbox  : {ver['safety_status']}")
    print(f"- Untrusted Code Status  : {ver['code_execution_status']}")
    print(f"- Regression Check       : {ver['regression_status']}")
    print("=" * 80)
    print("EduAdapt Adaptive Learning Session Demonstration Completed.")
    print("=" * 80)

    return result


def main():
    args = parse_args()
    run_full_demo(
        student_id=args.student_id,
        topic=args.topic,
        provider=args.provider,
        model=args.model,
        ollama_url=args.ollama_url,
        top_k=args.top_k,
        json_output=args.json_output,
    )


if __name__ == "__main__":
    main()
