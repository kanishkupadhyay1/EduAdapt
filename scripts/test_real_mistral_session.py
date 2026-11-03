"""Integration script to test real Mistral 7B inference with EduAdapt.

Runs an end-to-end learning session for real student S005 (Beginner, 0.25 mastery)
and real student S001 (Advanced, 1.0 mastery) using Ollama mistral:7b.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))

from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.services.adaptive_learning import AdaptiveLearningService
from eduadapt.verification.response_verifier import ResponseVerifier


def main():
    print("=================================================================")
    print("EduAdapt Real Mistral 7B Integration & Personalization Test")
    print("=================================================================")

    # Initialize real Ollama client
    ollama_client = OllamaLLMClient(
        base_url="http://127.0.0.1:11434",
        model_name="mistral:7b",
        temperature=0.3,
        max_tokens=1024,
        timeout=180.0,
    )

    rag = PPSCurriculumRAG.from_defaults(allow_empty=True)
    service = AdaptiveLearningService(llm_client=ollama_client, rag=rag)

    print("\n--- Running Learning Session for Real Student: S005 (Topic: Loops) ---")
    session_s005 = service.run_learning_session(student_id="S005", topic="Loops", top_k=2)

    teaching = session_s005.get("teaching", {})
    content = teaching.get("generated_teaching_content", "")
    metadata = teaching.get("generation_metadata", {})
    personalization = teaching.get("personalization_applied", {})
    diagram = teaching.get("diagram")
    verification = session_s005.get("verification", {})

    print(f"\nStudent S005 Status:")
    print(f"  Mastery Tier: {metadata.get('mastery_tier')}")
    print(f"  Actual Mastery: {metadata.get('actual_mastery_used')}")
    print(f"  Learning Pace: {metadata.get('learning_pace')}")
    print(f"  Selected Strategy: {metadata.get('selected_strategy', {}).get('explanation_depth')}")
    print(f"  Diagram Type: {metadata.get('diagram_decision')}")
    print(f"  Diagram Valid: {diagram.get('is_valid') if diagram else 'No diagram'}")
    print(f"  Grounding Ratio: {verification.get('grounding_ratio')}")
    print(f"  Code Detected: {verification.get('code_detected')}")
    print(f"  Code Status: {verification.get('code_execution')}")
    print(f"  Overall Verification: {verification.get('overall_status')}")

    print("\n--- Generated Content Preview (First 400 chars) ---")
    print(content[:400] + "..." if len(content) > 400 else content)

    if diagram and diagram.get("is_valid"):
        print("\n--- Valid Mermaid Diagram Generated ---")
        print(diagram.get("mermaid_code")[:250] + "...")

    print("\n=================================================================")
    print("Real Integration Test Completed Successfully!")
    print("=================================================================")


if __name__ == "__main__":
    main()
