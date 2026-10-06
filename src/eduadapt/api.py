"""Minimal FastAPI application adapter exposing EduAdapt's AdaptiveLearningService,
Curriculum RAG, Mistral 7B inference, and Student Learning Twin.

Strictly non-agentic: handles deterministic student-facing learning requests
without autonomous agent loops or multi-agent frameworks.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from eduadapt.adapters.student_twin_adapter import LearningTwinAdapter
from eduadapt.config import get_settings
from eduadapt.inference.base import BaseLLMClient, MockLLMClient
from eduadapt.inference.ollama import (
    OllamaConnectionError,
    OllamaLLMClient,
    OllamaTimeoutError,
)
from eduadapt.interfaces.rag import RAGContext
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.services.adaptive_learning import (
    STATIC_PPS_ASSESSMENT_BANK,
    AdaptiveLearningService,
)
from member3.student_state import get_student_state


app = FastAPI(
    title="EduAdapt API",
    description="Student-facing educational API for Programming for Problem Solving (PPS).",
    version="1.0.0",
)

# Enable CORS for local and web frontend deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance holder
_service: Optional[AdaptiveLearningService] = None


def get_service(provider: Optional[str] = None, model: Optional[str] = None) -> AdaptiveLearningService:
    """Initialize or retrieve the AdaptiveLearningService using application settings or overrides."""
    global _service
    settings = get_settings()
    eff_provider = (provider or settings.llm_provider or "ollama").strip().lower()
    eff_model = model or settings.llm_model_name or "mistral:7b"

    # If singleton service matches the desired provider and model, reuse it
    if _service is not None:
        current_client = _service.llm_client
        if eff_provider == "ollama" and isinstance(current_client, OllamaLLMClient) and current_client.model_name == eff_model:
            return _service
        if eff_provider == "mock" and isinstance(current_client, MockLLMClient) and current_client.model_name == eff_model:
            return _service

    llm_client: BaseLLMClient
    if eff_provider == "ollama":
        llm_client = OllamaLLMClient(
            base_url=settings.llm_api_base or "http://localhost:11434",
            model_name=eff_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
        )
    else:
        llm_client = MockLLMClient(model_name=eff_model)

    rag = PPSCurriculumRAG.from_defaults(allow_empty=True)
    svc = AdaptiveLearningService(llm_client=llm_client, rag=rag)
    if _service is None or (provider is None and model is None):
        _service = svc
    return svc


class LearningSessionRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Curriculum topic")
    top_k: int = Field(default=3, description="RAG retrieval count", ge=1, le=10)
    provider: Optional[str] = Field(default="ollama", description="LLM provider: 'ollama' or 'mock'")
    model: Optional[str] = Field(default="mistral:7b", description="LLM model name")
    assessment_submission: Optional[Dict[str, Any]] = None


class TutorChatRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Active curriculum topic")
    message: str = Field(..., description="Student inquiry or question")
    prompt_variation: Optional[str] = Field(
        default=None,
        description="Shortcut mode: 'simpler', 'example', 'practice_question'",
    )


class AssessmentSubmitRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Curriculum topic")
    selected_option: str = Field(..., description="Student selected option, e.g. 'B'")
    time_taken_seconds: int = Field(default=25, description="Time taken in seconds")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "EduAdapt"}


@app.get("/api/student/{student_id}")
def get_student_profile(student_id: str) -> Dict[str, Any]:
    state = get_student_state(student_id)
    if not state:
        return {
            "student_id": student_id,
            "found": False,
            "mastery": 0.0,
            "accuracy": 0.0,
            "learning_pace": "moderate",
            "recommended_difficulty": "Medium",
            "predicted_mastery_level": "Unknown",
            "learning_style": "balanced",
        }
    return {
        **state,
        "found": True,
        "learning_style": "balanced",
    }


@app.post("/api/session/generate")
def generate_session(req: LearningSessionRequest) -> Dict[str, Any]:
    try:
        service = get_service(provider=req.provider, model=req.model)
        result = service.run_learning_session(
            student_id=req.student_id,
            topic=req.topic,
            top_k=req.top_k,
            generate_roadmap=True,
            generate_feedback=True,
            assessment_submission=req.assessment_submission,
        )
        return result
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        raise HTTPException(
            status_code=503,
            detail="EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate learning session: {str(e)}")


@app.post("/api/tutor/chat")
def tutor_chat(req: TutorChatRequest) -> Dict[str, Any]:
    """Curriculum-grounded AI Tutor dialogue using the existing LLM and RAG pipelines."""
    service = get_service()
    
    # 1. Fetch student state
    adapter = LearningTwinAdapter(default_topic=req.topic)
    profile = adapter.get_profile(student_id=req.student_id, topic=req.topic)
    
    mastery_desc = "Advanced"
    pace_desc = "Fast"
    if profile:
        pace_desc = profile.preferred_pace
        score = profile.mastery_levels.get(req.topic, 1.0)
        mastery_desc = "Advanced" if score >= 0.7 else ("Intermediate" if score >= 0.4 else "Beginner")

    # 2. Retrieve curriculum RAG context
    curriculum_context = "PPS Curriculum Context for " + req.topic
    retrieved_sources: List[Dict[str, Any]] = []
    if service.rag:
        try:
            rag_ctx: RAGContext = service.rag.retrieve(query=f"{req.topic} {req.message}", top_k=3)
            curriculum_context = rag_ctx.format_for_prompt()
            for doc in rag_ctx.documents:
                retrieved_sources.append({
                    "source": doc.source,
                    "slide_or_page": doc.page,
                    "unit": doc.module,
                    "topic": doc.topic,
                })
        except Exception:
            pass

    # 3. Handle prompt variations
    user_query = req.message
    if req.prompt_variation == "simpler":
        instruction = "Explain this concept in very simple, intuitive terms with a beginner-friendly analogy and clear C snippet."
    elif req.prompt_variation == "example":
        instruction = "Provide a clean, step-by-step practical C programming example with detailed comments."
    elif req.prompt_variation == "practice_question":
        instruction = "Provide a short, targeted conceptual question with 4 options to test understanding of this specific topic."
    else:
        instruction = "Provide a direct, pedagogically tailored explanation grounded in the PPS curriculum."

    full_prompt = (
        f"You are the EduAdapt AI Tutor for the Programming for Problem Solving (PPS) course.\n"
        f"Topic: {req.topic}\n"
        f"Student ID: {req.student_id}\n"
        f"Current Level: {mastery_desc} (Pace: {pace_desc})\n\n"
        f"PPS Curriculum Reference Context:\n{curriculum_context}\n\n"
        f"Pedagogical Instruction: {instruction}\n"
        f"Student Question: {user_query}\n\n"
        f"Respond clearly, concisely, and helpfully. Include syntactically correct C code blocks if helpful."
    )

    try:
        gen_res = service.llm_client.generate(prompt=full_prompt)
        return {
            "reply": gen_res.content,
            "topic": req.topic,
            "student_id": req.student_id,
            "model": gen_res.model_name,
            "curriculum_sources": retrieved_sources,
        }
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        raise HTTPException(
            status_code=503,
            detail="EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tutor generation error: {str(e)}")


@app.get("/api/assessment/{student_id}/{topic}")
def get_assessment_for_topic(student_id: str, topic: str) -> Dict[str, Any]:
    """Retrieve verified PPS assessment question for the topic."""
    assessment_meta = STATIC_PPS_ASSESSMENT_BANK.get(
        topic,
        STATIC_PPS_ASSESSMENT_BANK["Pointers"],
    )
    return {
        "student_id": student_id,
        "topic": topic,
        "question": assessment_meta["question"],
        "options": assessment_meta["options"],
        "correct_option": assessment_meta["correct_option"],
        "explanation": assessment_meta["explanation"],
    }


@app.post("/api/assessment/submit")
def submit_assessment(req: AssessmentSubmitRequest) -> Dict[str, Any]:
    """Submit answer, evaluate accuracy, and recompute Learning Twin state."""
    service = get_service()
    assessment_meta = STATIC_PPS_ASSESSMENT_BANK.get(
        req.topic,
        STATIC_PPS_ASSESSMENT_BANK["Pointers"],
    )

    is_correct = (req.selected_option.strip().upper() == assessment_meta["correct_option"].strip().upper())
    score = 95 if is_correct else 35
    submission_data = {
        "correct": 1 if is_correct else 0,
        "score": score,
        "attempts": 1,
        "time_taken": req.time_taken_seconds,
    }

    # Run session with the genuine student submission to update the Learning Twin
    session_result = service.run_learning_session(
        student_id=req.student_id,
        topic=req.topic,
        top_k=3,
        generate_roadmap=True,
        generate_feedback=True,
        assessment_submission=submission_data,
    )

    return {
        "is_correct": is_correct,
        "score": score,
        "selected_option": req.selected_option,
        "correct_option": assessment_meta["correct_option"],
        "explanation": assessment_meta["explanation"],
        "time_taken_seconds": req.time_taken_seconds,
        "feedback": session_result.get("feedback", {}).get("feedback"),
        "updated_learning_state": session_result.get("learning_state"),
        "updated_student": session_result.get("student"),
        "roadmap": session_result.get("roadmap"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eduadapt.api:app", host="0.0.0.0", port=8000, reload=True)
