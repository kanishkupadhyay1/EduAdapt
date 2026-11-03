"""Test live teaching generation with warm Mistral 7B for real students S005 and S001."""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))

from eduadapt.adapters.student_twin_adapter import LearningTwinAdapter
from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.teaching.generator import PersonalizedContentGenerator
from eduadapt.verification.response_verifier import ResponseVerifier
from member3.student_state import get_student_state


def test_student(student_id: str, topic: str):
    print(f"\n=======================================================")
    print(f"Testing Real Student: {student_id} on Topic: {topic}")
    print(f"=======================================================")

    adapter = LearningTwinAdapter(default_topic=topic)
    profile = adapter.get_profile(student_id=student_id, topic=topic)
    raw_state = get_student_state(student_id)

    client = OllamaLLMClient(
        base_url="http://127.0.0.1:11434",
        model_name="mistral:7b",
        temperature=0.3,
        max_tokens=600,
        timeout=180.0,
    )
    rag = PPSCurriculumRAG.from_defaults(allow_empty=True)
    generator = PersonalizedContentGenerator(llm_client=client, rag=rag)

    res = generator.generate_for_student(
        topic=topic,
        student_profile=profile,
        learning_state=raw_state,
    )

    print(f"Personalization Applied:")
    for k, v in res.metadata.get("personalization_applied", {}).items():
        print(f"  {k}: {v}")

    diag = res.metadata.get("diagram")
    if diag:
        print(f"\nDiagram Result:")
        print(f"  Valid: {diag.get('is_valid')}")
        print(f"  Type: {diag.get('diagram_type')}")
        if diag.get("is_valid"):
            print(f"  Mermaid Code:\n{diag.get('mermaid_code')}")

    # Verify with ResponseVerifier
    v_res = ResponseVerifier.verify_response(
        response_text=res.content,
        retrieved_chunks=[{"source": "PPS Slides", "preview": "loops in C"}],
        topic=topic,
    )
    print(f"\nResponse Verification:")
    print(f"  Grounding Status: {v_res.grounding_status}")
    print(f"  Code Detected: {v_res.code_detected}")
    print(f"  Code Lines: {v_res.extracted_code_lines}")
    print(f"  Safety Status: {v_res.safety_status}")
    print(f"  Code Execution: {v_res.code_execution_status}")

    print(f"\nGenerated Teaching Preview (first 300 chars):")
    print(res.content[:300] + "...")
    return res


if __name__ == "__main__":
    # Test real beginner student S005
    test_student("S005", "Loops")
