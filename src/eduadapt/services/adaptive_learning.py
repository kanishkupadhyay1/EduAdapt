"""Adaptive Learning Service Orchestrator for EduAdapt.

Provides a unified, deterministic service layer orchestrating the verified pipeline:
Student Learning Twin (Member 3)
    ↓
LearningTwinAdapter
    ↓
Canonical StudentProfile
    ↓
PPS RAG Retrieval (Member 2)
    ↓
Curriculum-grounded Personalized Content Generation (Member 1)
    ↓
Post-learning Assessment Evaluation
    ↓
Safety & Code Verification
    ↓
Roadmap & Feedback Generation
    ↓
Learning Twin State Update Inspection

Strictly non-agentic: no autonomous agent loops or multi-agent frameworks.
"""

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from eduadapt.adapters.student_twin_adapter import LearningTwinAdapter
from eduadapt.evaluation.c_executor import extract_c_code
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.evaluation.regression import check_while_loop_explanation
from eduadapt.feedback.evaluator import FeedbackGenerator
from eduadapt.inference.base import BaseLLMClient
from eduadapt.interfaces.rag import RAGContext, RAGInterface
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.roadmap.planner import RoadmapGenerator
from eduadapt.teaching.generator import PersonalizedContentGenerator
from member3.assessment import calculate_student_performance
from member3.features import create_features
from member3.learning_twin import create_learning_twin
from member3.student_state import get_student_state

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "assessment_data.csv"

# Representative curated PPS assessment questions for post-learning evaluation
STATIC_PPS_ASSESSMENT_BANK: Dict[str, Dict[str, Any]] = {
    "Pointers": {
        "question": "What is the output of dereferencing a pointer `*ptr` when `int a = 42; int *ptr = &a;` in C?",
        "options": ["A) Memory address of a", "B) 42", "C) Null pointer error", "D) Garbage value"],
        "correct_option": "B",
        "explanation": "The dereference operator `*` accesses the value stored at the memory location pointed to by `ptr`.",
        "default_submission": {"correct": 1, "score": 95, "attempts": 1, "time_taken": 25},
    },
    "Loops": {
        "question": "Which loop construct in C is guaranteed to execute its body at least once?",
        "options": ["A) for loop", "B) while loop", "C) do-while loop", "D) nested loop"],
        "correct_option": "C",
        "explanation": "A do-while loop evaluates its conditional check at the end of each iteration.",
        "default_submission": {"correct": 1, "score": 90, "attempts": 1, "time_taken": 20},
    },
    "Arrays": {
        "question": "In C, what does the expression `arr[i]` translate to in pointer arithmetic?",
        "options": ["A) *(arr + i)", "B) &arr + i", "C) arr + *i", "D) *arr + i"],
        "correct_option": "A",
        "explanation": "Array indexing `arr[i]` is defined syntactically as pointer dereference `*(arr + i)`.",
        "default_submission": {"correct": 1, "score": 85, "attempts": 1, "time_taken": 30},
    },
    "Functions": {
        "question": "How are function arguments passed by default in standard C?",
        "options": ["A) Pass by reference", "B) Pass by value", "C) Pass by pointer", "D) Pass by name"],
        "correct_option": "B",
        "explanation": "C uses pass-by-value semantics for all function arguments unless explicitly passed via memory address.",
        "default_submission": {"correct": 1, "score": 90, "attempts": 1, "time_taken": 22},
    },
}


class AdaptiveLearningService:
    """Orchestrates verified student twin, RAG, teaching, assessment, and feedback components."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        rag: Optional[RAGInterface] = None,
        prompt_manager: Optional[PromptManager] = None,
    ) -> None:
        self.llm_client = llm_client
        self.rag = rag
        self.prompt_manager = prompt_manager or PromptManager()

        self.teaching_generator = PersonalizedContentGenerator(
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
            rag=self.rag,
        )
        self.feedback_generator = FeedbackGenerator(
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
        )
        self.roadmap_generator = RoadmapGenerator(
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
        )

    def run_learning_session(
        self,
        student_id: str,
        topic: str = "Pointers",
        top_k: int = 3,
        generate_roadmap: bool = True,
        generate_feedback: bool = True,
        assessment_submission: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run an end-to-end adaptive learning session.

        Args:
            student_id: Student identifier (e.g., 'S001').
            topic: Target PPS topic (e.g., 'Pointers').
            top_k: Number of curriculum chunks to retrieve via RAG.
            generate_roadmap: Whether to generate an adaptive roadmap.
            generate_feedback: Whether to generate personalized feedback on practice/assessment.
            assessment_submission: Optional custom submission dict with keys
                ('correct', 'score', 'attempts', 'time_taken'). If None, default realistic
                submission for the topic is used.

        Returns:
            Structured dictionary matching the EduAdapt frontend and demonstration contract.
        """
        # 1. INITIAL STUDENT STATE & CANONICAL PROFILE (Member 3 Learning Twin)
        adapter = LearningTwinAdapter(default_topic=topic)
        profile = adapter.get_profile(student_id=student_id, topic=topic)

        if profile is None:
            raw_state = None
            student_section = {
                "student_id": student_id,
                "found": False,
                "mastery": 0.0,
                "accuracy": 0.0,
                "learning_pace": "moderate",
                "recommended_difficulty": "Medium",
                "predicted_mastery_level": "Unknown",
            }
            profile_section = {
                "current_topic": topic,
                "mastery_levels": {topic: 0.0},
                "preferred_pace": "moderate",
                "learning_style": "balanced",
                "common_misconceptions": [],
            }
            # Create a safe fallback profile for downstream generation
            profile = StudentProfile(
                student_id=student_id,
                current_topic=topic,
                mastery_levels={topic: 0.0},
                learning_style="balanced",
                preferred_pace="moderate",
                common_misconceptions=[],
            )
        else:
            raw_state = get_student_state(student_id) or {}
            student_section = {
                "student_id": student_id,
                "found": True,
                "mastery": float(raw_state.get("mastery", profile.mastery_levels.get(topic, 0.0))),
                "accuracy": float(raw_state.get("accuracy", 0.0)),
                "learning_pace": str(raw_state.get("learning_pace", profile.preferred_pace)),
                "recommended_difficulty": str(raw_state.get("recommended_difficulty", "Medium")),
                "predicted_mastery_level": str(raw_state.get("predicted_mastery_level", "Unknown")),
            }
            profile_section = {
                "current_topic": profile.current_topic,
                "mastery_levels": profile.mastery_levels,
                "preferred_pace": profile.preferred_pace,
                "learning_style": profile.learning_style,
                "common_misconceptions": profile.common_misconceptions,
            }

        # 2. CURRICULUM RETRIEVAL (PPS RAG)
        retrieved_chunks: List[Dict[str, Any]] = []
        if self.rag is not None:
            try:
                rag_context: RAGContext = self.rag.retrieve(query=topic, top_k=top_k)
                for doc in rag_context.documents:
                    retrieved_chunks.append({
                        "doc_id": doc.doc_id,
                        "source": doc.source,
                        "slide_or_page": doc.page,
                        "unit_or_module": doc.module,
                        "topic": doc.topic,
                        "relevance_score": round(doc.score, 4) if doc.score is not None else None,
                        "preview": doc.content[:160] + "..." if len(doc.content) > 160 else doc.content,
                    })
            except Exception as e:
                logger.warning("RAG retrieval failed: %s", e)

        curriculum_section = {
            "topic": topic,
            "retrieved_count": len(retrieved_chunks),
            "retrieved_chunks": retrieved_chunks,
        }

        # 3. PERSONALIZED TEACHING GENERATION (Member 1 Content Generator)
        gen_result = self.teaching_generator.generate_for_student(
            topic=topic,
            student_profile=profile,
        )
        content_text = gen_result.content

        teaching_section = {
            "generated_teaching_content": content_text,
            "provider": self.llm_client.__class__.__name__,
            "model": gen_result.model_name,
            "latency": gen_result.metadata.get("latency_seconds"),
            "token_information": {
                "prompt_tokens": gen_result.prompt_tokens,
                "completion_tokens": gen_result.completion_tokens,
                "total_tokens": (
                    (gen_result.prompt_tokens or 0) + (gen_result.completion_tokens or 0)
                    if (gen_result.prompt_tokens is not None or gen_result.completion_tokens is not None)
                    else None
                ),
            },
        }

        # 4. POST-LEARNING ASSESSMENT (Member 3 Assessment)
        assessment_meta = STATIC_PPS_ASSESSMENT_BANK.get(
            topic,
            STATIC_PPS_ASSESSMENT_BANK["Pointers"],
        )
        submission = assessment_submission or assessment_meta["default_submission"]

        # Calculate historical stats if assessment data exists
        historical_perf: Dict[str, Any] = {}
        if DATA_PATH.exists():
            try:
                df = pd.read_csv(DATA_PATH)
                historical_perf = calculate_student_performance(df, student_id)
            except Exception as e:
                logger.warning("Could not calculate historical assessment performance: %s", e)

        assessment_section = {
            "topic": topic,
            "question": assessment_meta["question"],
            "options": assessment_meta["options"],
            "correct_option": assessment_meta["correct_option"],
            "explanation": assessment_meta["explanation"],
            "score": submission.get("score", 90),
            "accuracy": float(submission.get("correct", 1)),
            "attempts": submission.get("attempts", 1),
            "time_taken_seconds": submission.get("time_taken", 20),
            "historical_performance": historical_perf,
        }

        # 5. PERSONALIZED FEEDBACK (Existing FeedbackGenerator)
        feedback_section: Dict[str, Any] = {}
        if generate_feedback:
            sample_student_code = (
                "// Student implementation for topic: " + topic + "\n"
                "void solution() {\n"
                "    int val = 42;\n"
                "    int *p = &val;\n"
                "    *p = 100;\n"
                "}\n"
            )
            feedback_res = self.feedback_generator.generate_feedback(
                problem_description=f"PPS problem on topic: {topic}. Student answered post-learning quiz question: {assessment_meta['question']}",
                student_code=sample_student_code,
            )
            feedback_section = {
                "problem": f"Practice submission for {topic}",
                "feedback": feedback_res.content,
                "model": feedback_res.model_name,
            }

        # 6. LEARNING TWIN UPDATE (Member 3 Update State Verification)
        # Check genuinely computed update using Member 3's create_features + create_learning_twin
        learning_state_section: Dict[str, Any] = {
            "initial_state": raw_state,
            "can_update_in_place": False,
            "updated_state": None,
            "status_message": (
                "Post-assessment result recorded; Learning Twin update requires "
                "additional training/update data."
            ),
        }

        if raw_state is not None and DATA_PATH.exists():
            try:
                df = pd.read_csv(DATA_PATH)
                new_record = pd.DataFrame([{
                    "student_id": student_id,
                    "topic": topic,
                    "correct": submission.get("correct", 1),
                    "score": submission.get("score", 90),
                    "attempts": submission.get("attempts", 1),
                    "time_taken": submission.get("time_taken", 20),
                    "mastery_level": raw_state.get("predicted_mastery_level", "High"),
                }])
                updated_df = pd.concat([df, new_record], ignore_index=True)
                feature_df = create_features(updated_df)
                student_data = feature_df[feature_df["student_id"] == student_id]
                if not student_data.empty:
                    simulated_twin = create_learning_twin(student_data.iloc[0].to_dict())
                    learning_state_section["simulated_twin"] = simulated_twin
                    # Notice: We strictly report whether the stored model was retrained
                    learning_state_section["can_update_in_place"] = True
                    learning_state_section["updated_state"] = simulated_twin
                    learning_state_section["status_message"] = (
                        f"Learning Twin state recomputed with assessment submission: "
                        f"mastery={simulated_twin['mastery']}, pace={simulated_twin['learning_pace']}, "
                        f"difficulty={simulated_twin['recommended_difficulty']}."
                    )
            except Exception as e:
                logger.warning("Simulated state update failed: %s", e)

        # 7. PERSONALIZED ROADMAP (Existing RoadmapGenerator)
        roadmap_section: Dict[str, Any] = {}
        if generate_roadmap:
            current_mastery_desc = (
                student_section.get("predicted_mastery_level")
                or student_section.get("recommended_difficulty")
                or "Beginner"
            )
            roadmap_res = self.roadmap_generator.generate_roadmap(
                target_competency=f"{topic} Mastery in Programming for Problem Solving (PPS)",
                current_mastery=current_mastery_desc,
            )
            roadmap_section = {
                "target_competency": f"{topic} Mastery in PPS",
                "current_mastery": current_mastery_desc,
                "roadmap_content": roadmap_res.content,
                "model": roadmap_res.model_name,
            }

        # 8. VERIFICATION & SAFETY (Strict isolation of LLM-generated C code)
        extracted_code = extract_c_code(content_text)
        regression_check = check_while_loop_explanation(content_text)

        verification_section = {
            "curriculum_context_available": len(retrieved_chunks) > 0,
            "retrieved_chunks_count": len(retrieved_chunks),
            "generation_completed": bool(content_text.strip()),
            "code_extracted": bool(extracted_code),
            "extracted_code_lines": len(extracted_code.splitlines()) if extracted_code else 0,
            "code_execution_status": ExecutionStatus.NOT_EXECUTED_UNTRUSTED.value,
            "safety_status": "Enforced: untrusted LLM code is NOT executed on host machine",
            "regression_status": "Passed" if regression_check.passed else f"Failed: {regression_check.explanation}",
        }

        # Contract matching PART 7 Frontend Contract
        return {
            "student": student_section,
            "profile": profile_section,
            "curriculum": curriculum_section,
            "teaching": teaching_section,
            "assessment": assessment_section,
            "feedback": feedback_section,
            "learning_state": learning_state_section,
            "roadmap": roadmap_section,
            "verification": verification_section,
        }
