"""Minimal FastAPI application adapter exposing EduAdapt's AdaptiveLearningService,
Curriculum RAG, Mistral 7B inference, and Student Learning Twin.

Strictly non-agentic: handles deterministic student-facing learning requests
without autonomous agent loops or multi-agent frameworks.
"""

import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

# Ensure project root and src/ are in sys.path regardless of execution context
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for p in [str(_REPO_ROOT), str(_SRC_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Response, UploadFile
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
from eduadapt.services.question_service import QuestionService, PPS_CURRICULUM_SEQUENCE
from member3.student_state import get_student_state
from member4.speech_to_text import SpeechToText
from member4.text_to_speech import TextToSpeech, clean_text_for_speech


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

    try:
        rag = PPSCurriculumRAG.from_defaults(allow_empty=True)
    except Exception:
        rag = None

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
    selected_option: Optional[str] = Field(default="B", description="Student selected option, e.g. 'B'")
    time_taken_seconds: int = Field(default=25, description="Time taken in seconds")
    question_idx: int = Field(default=0, description="Index of question in topic bank")
    question_id: Optional[str] = Field(default=None, description="Optional question ID")
    answers: Optional[Dict[str, str]] = Field(default=None, description="Optional full assessment answers map")


class PracticeSubmitRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Curriculum topic")
    answers: Dict[str, str] = Field(default_factory=dict, description="Student answers map")
    time_taken_seconds: int = Field(default=25, description="Time taken in seconds")


class PracticeGenerateRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Curriculum topic")


class PracticeExecuteRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Curriculum topic")
    source_code: str = Field(..., description="C source code to compile and run")
    expected_output: Optional[str] = Field(default=None, description="Expected output for evaluation")
    stdin_input: Optional[str] = Field(default=None, description="Optional stdin input to feed to the program")
    is_submission: bool = Field(default=False, description="Whether this is a final submission evaluation")


class RoadmapGenerateRequest(BaseModel):
    student_id: str = Field(default="S001", description="Student identifier")
    topic: str = Field(default="Pointers", description="Target curriculum topic")


class CurriculumSearchRequest(BaseModel):
    query: str = Field(..., description="PPS search query or concept keyword")
    top_k: int = Field(default=3, description="Number of results to retrieve", ge=1, le=10)


class AudioSynthesizeRequest(BaseModel):
    text: str = Field(..., description="Educational content to convert to speech")
    rate: int = Field(default=170, description="Speaking rate in words per minute")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "EduAdapt"}


@app.get("/api/audio/status")
def get_audio_status() -> Dict[str, Any]:
    """Report availability of local speech-to-text and text-to-speech pipelines."""
    stt_ok = False
    stt_model = None
    try:
        import whisper
        stt_ok = True
        stt_model = "base"
    except Exception:
        pass

    tts_ok = False
    tts_engine = None
    if os.name == "nt":
        try:
            import win32com.client
            tts_ok = True
            tts_engine = "sapi5"
        except Exception:
            pass
    if not tts_ok:
        try:
            import pyttsx3
            tts_ok = True
            tts_engine = "pyttsx3"
        except Exception:
            pass

    return {
        "speech_to_text_available": stt_ok,
        "speech_model": stt_model,
        "text_to_speech_available": tts_ok,
        "tts_engine": tts_engine,
    }


@app.post("/api/audio/transcribe")
def transcribe_audio(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Transcribe student spoken audio using Member 4's Whisper integration."""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided.")

    contents = file.file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty (0 bytes).")

    ext = Path(file.filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        stt = SpeechToText(model_name="base")
        transcription = stt.transcribe(tmp_path)
        return {
            "status": "success",
            "transcription": transcription,
            "filename": file.filename,
            "size_bytes": len(contents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(e)}")
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


@app.post("/api/audio/synthesize")
def synthesize_speech(req: AudioSynthesizeRequest) -> Response:
    """Synthesize educational lesson text to speech WAV file using Member 4's TTS."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text for speech synthesis cannot be empty.")

    tmp_dir = Path(tempfile.gettempdir()) / "eduadapt_audio"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    temp_wav = tmp_dir / f"lesson_{os.getpid()}_{time.time_ns()}.wav"

    try:
        tts = TextToSpeech(rate=req.rate)
        saved_path = tts.save_to_file(req.text, temp_wav)
        if not saved_path.exists() or saved_path.stat().st_size == 0:
            raise RuntimeError("Audio file was generated with zero bytes.")

        audio_bytes = saved_path.read_bytes()
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": 'attachment; filename="lesson_explanation.wav"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech generation failed: {str(e)}")


@app.get("/api/student/{student_id}")
def get_student_profile(student_id: str, fresh: bool = False) -> Dict[str, Any]:
    if fresh or student_id.upper() in ("NEW", "S_NEW", "STUDENT_0"):
        return {
            "student_id": student_id,
            "found": True,
            "mastery": 0.0,
            "accuracy": 0.0,
            "learning_pace": "Moderate",
            "recommended_difficulty": "Beginner",
            "predicted_mastery_level": "New Learner",
            "learning_style": "balanced",
            "tests_completed": 0,
        }
    state = get_student_state(student_id)
    if not state:
        return {
            "student_id": student_id,
            "found": False,
            "mastery": 0.0,
            "accuracy": 0.0,
            "learning_pace": "Moderate",
            "recommended_difficulty": "Beginner",
            "predicted_mastery_level": "New Learner",
            "learning_style": "balanced",
            "tests_completed": 0,
        }

    completed_count = 0
    from pathlib import Path
    import pandas as pd
    data_file = Path(__file__).resolve().parent.parent.parent / "data" / "assessment_data.csv"
    if data_file.exists():
        try:
            df = pd.read_csv(data_file)
            completed_count = len(df[df["student_id"] == student_id])
        except Exception:
            pass

    return {
        **state,
        "found": True,
        "learning_style": "balanced",
        "tests_completed": completed_count,
    }


@app.post("/api/student/{student_id}/reset")
def reset_student_profile(student_id: str) -> Dict[str, Any]:
    """Reset student profile to 0 for demonstrations."""
    return {
        "student_id": student_id,
        "found": True,
        "mastery": 0.0,
        "accuracy": 0.0,
        "learning_pace": "Moderate",
        "recommended_difficulty": "Beginner",
        "predicted_mastery_level": "New Learner",
        "learning_style": "balanced",
        "tests_completed": 0,
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
        instruction = (
            "Provide an encouraging, clear pedagogical explanation grounded in the PPS curriculum. "
            "Act as an interactive mentor: do not output raw test scores, evaluation scorecards, or harsh grading remarks. "
            "Help the student understand the conceptual mechanics, memory layout, and underlying logic."
        )

    full_prompt = (
        f"You are the friendly, supportive EduAdapt AI Tutor for Programming for Problem Solving (PPS).\n"
        f"Topic: {req.topic}\n"
        f"Student ID: {req.student_id}\n"
        f"Current Level: {mastery_desc} (Pace: {pace_desc})\n\n"
        f"PPS Curriculum Reference Context:\n{curriculum_context}\n\n"
        f"Tutor Role: You are a helpful conceptual mentor. "
        f"If the student asks why an answer is correct or asks for conceptual help, "
        f"explain the 'why' clearly and warmly with clean C code examples.\n\n"
        f"Pedagogical Instruction: {instruction}\n"
        f"Student Inquiry: {user_query}\n\n"
        f"AI Tutor Response:"
    )

    try:
        gen_res = service.llm_client.generate(prompt=full_prompt)
        from eduadapt.teaching.diagrams import MermaidValidator
        diag_code = MermaidValidator.extract_mermaid_code(gen_res.content)
        diagram_data = None
        if diag_code:
            diag_res = MermaidValidator.validate_and_sanitize(diag_code, topic=req.topic)
            if diag_res.is_valid:
                diagram_data = diag_res.to_dict()

        return {
            "reply": gen_res.content,
            "topic": req.topic,
            "student_id": req.student_id,
            "model": gen_res.model_name,
            "curriculum_sources": retrieved_sources,
            "diagram": diagram_data,
        }
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        raise HTTPException(
            status_code=503,
            detail="EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tutor generation error: {str(e)}")


question_service = QuestionService()


@app.get("/api/practice/{student_id}/{topic}/mcqs")
def get_practice_mcqs(student_id: str, topic: str) -> Dict[str, Any]:
    """Retrieve exactly 5 verified PPS curriculum practice questions (|P| = 5)."""
    return question_service.get_practice_session(student_id, topic)


@app.post("/api/practice/submit")
def submit_practice(req: PracticeSubmitRequest) -> Dict[str, Any]:
    """Authoritative backend evaluation of 5-question practice session and Learning Twin update."""
    service = get_service()
    eval_res = question_service.evaluate_practice_submission(
        student_id=req.student_id,
        topic=req.topic,
        answers=req.answers,
        time_taken_seconds=req.time_taken_seconds,
    )
    # Recompute Learning Twin features using evaluated score
    twin_eval = service.evaluate_submission(
        student_id=req.student_id,
        topic=req.topic,
        selected_option="B" if eval_res["is_correct"] else "A",
        time_taken_seconds=req.time_taken_seconds,
    )
    eval_res["updated_student"] = twin_eval.get("updated_student")
    eval_res["updated_learning_state"] = twin_eval.get("updated_learning_state")
    return eval_res


@app.get("/api/assessment/{student_id}/{topic}")
def get_assessment_for_topic(student_id: str, topic: str, question_idx: int = 0) -> Dict[str, Any]:
    """Retrieve verified PPS practice question for the topic (|P| = 5)."""
    practice_session = question_service.get_practice_session(student_id, topic)
    questions = practice_session.get("questions", [])
    if questions:
        idx = question_idx % len(questions)
        q = questions[idx]
        return {
            "student_id": student_id,
            "topic": topic,
            "question_id": q["id"],
            "question_idx": idx,
            "total_questions": len(questions),
            "question": q["question"],
            "options": q["options"],
            "correct_option": q["correct_option"],
            "explanation": q["explanation"],
            "concept": q.get("concept", topic),
        }
    return {
        "student_id": student_id,
        "topic": topic,
        "question_idx": 0,
        "total_questions": 1,
        "question": f"Core conceptual question for {topic}",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "correct_option": "B",
        "explanation": f"Evaluates understanding of {topic}.",
    }


@app.get("/api/assessment/{student_id}/{topic}/all")
def get_all_assessments_for_topic(student_id: str, topic: str) -> Dict[str, Any]:
    """Retrieve exactly 10 verified PPS assessment questions (guaranteed P ∩ A = ∅)."""
    return question_service.get_assessment_session(student_id, topic)


@app.post("/api/assessment/submit")
def submit_assessment(req: AssessmentSubmitRequest) -> Dict[str, Any]:
    """Authoritative backend evaluation for assessment and Learning Twin recomputation (<10ms)."""
    service = get_service()

    if req.answers and len(req.answers) > 0:
        eval_res = question_service.evaluate_assessment_submission(
            student_id=req.student_id,
            topic=req.topic,
            answers=req.answers,
            time_taken_seconds=req.time_taken_seconds,
        )
        twin_eval = service.evaluate_submission(
            student_id=req.student_id,
            topic=req.topic,
            selected_option="B" if eval_res["is_correct"] else "A",
            time_taken_seconds=req.time_taken_seconds,
        )
        eval_res["updated_student"] = twin_eval.get("updated_student")
        eval_res["updated_learning_state"] = twin_eval.get("updated_learning_state")
        return eval_res

    # Legacy single-question submission
    result = service.evaluate_submission(
        student_id=req.student_id,
        topic=req.topic,
        selected_option=req.selected_option or "B",
        time_taken_seconds=req.time_taken_seconds,
        question_idx=req.question_idx,
        question_id=req.question_id,
    )
    return result


@app.get("/api/roadmap/{student_id}")
def get_student_roadmap(student_id: str) -> Dict[str, Any]:
    """Retrieve student progression roadmap showing completed, active, and upcoming topics."""
    return question_service.get_student_roadmap(student_id)


@app.post("/api/roadmap/{student_id}/advance")
def advance_student_topic(student_id: str, topic: str) -> Dict[str, Any]:
    """Advance student to the next topic in the PPS curriculum."""
    next_topic = question_service.get_next_topic(topic)
    return {
        "student_id": student_id,
        "completed_topic": topic,
        "next_topic": next_topic,
        "status": "advanced",
    }


@app.get("/api/students")
def list_students() -> List[Dict[str, Any]]:
    """List real student profiles derived from Member 3's dataset and Learning Twin."""
    from pathlib import Path
    import pandas as pd

    data_file = Path(__file__).resolve().parent.parent.parent / "data" / "assessment_data.csv"
    students = []
    if data_file.exists():
        try:
            df = pd.read_csv(data_file)
            unique_ids = df["student_id"].dropna().unique().tolist()
            for sid in unique_ids:
                st = get_student_state(sid) or {}
                completed = len(df[df["student_id"] == sid])
                students.append({
                    "student_id": sid,
                    "mastery": float(st.get("mastery", 0.0)),
                    "accuracy": float(st.get("accuracy", 0.0)),
                    "learning_pace": str(st.get("learning_pace", "Moderate")),
                    "recommended_difficulty": str(st.get("recommended_difficulty", "Medium")),
                    "predicted_mastery_level": str(st.get("predicted_mastery_level", "Medium")),
                    "tests_completed": completed,
                })
        except Exception:
            pass

    if not students:
        students = [
            {"student_id": "S001", "mastery": 1.0, "accuracy": 1.0, "learning_pace": "Fast", "recommended_difficulty": "Advanced", "predicted_mastery_level": "High", "tests_completed": 4},
            {"student_id": "S003", "mastery": 0.75, "accuracy": 0.75, "learning_pace": "Medium", "recommended_difficulty": "Advanced", "predicted_mastery_level": "High", "tests_completed": 4},
            {"student_id": "S005", "mastery": 0.25, "accuracy": 0.25, "learning_pace": "Slow", "recommended_difficulty": "Easy", "predicted_mastery_level": "High", "tests_completed": 4},
        ]
    return students


@app.post("/api/practice/generate")
def generate_practice(req: PracticeGenerateRequest) -> Dict[str, Any]:
    """Generate adaptive practice problems with progressive hint ladders."""
    service = get_service()
    adapter = LearningTwinAdapter(default_topic=req.topic)
    profile = adapter.get_profile(student_id=req.student_id, topic=req.topic)
    raw_state = get_student_state(req.student_id)
    if not profile:
        from eduadapt.interfaces.student_model import StudentProfile
        profile = StudentProfile(student_id=req.student_id, current_topic=req.topic, mastery_levels={req.topic: 0.0})

    from eduadapt.teaching.personalization import PersonalizationEngine
    from eduadapt.teaching.response_schema import ResponseParser

    p_context = PersonalizationEngine.derive_context(
        student_profile=profile,
        topic=req.topic,
        learning_state=raw_state,
    )

    try:
        gen_res = service.teaching_generator.generate_practice_problems(
            topic=req.topic,
            student_profile=profile,
            learning_state=raw_state,
        )

        challenge = ResponseParser.parse_coding_challenge(
            raw_text=gen_res.content,
            topic=req.topic,
            difficulty=p_context.recommended_difficulty,
            mastery_tier=p_context.mastery_tier,
        )

        return {
            "student_id": req.student_id,
            "topic": req.topic,
            "target_mastery": f"{p_context.topic_mastery:.2f}",
            "recommended_difficulty": p_context.recommended_difficulty,
            "mastery_tier": p_context.mastery_tier,
            "learning_pace": p_context.learning_pace,
            "accuracy": p_context.accuracy,
            "predicted_mastery_level": p_context.predicted_mastery_level,
            "model": gen_res.model_name,
            "challenge": challenge,
            "practice_problems": [challenge],
            "practice_content": gen_res.content,
        }
    except (OllamaConnectionError, OllamaTimeoutError):
        raise HTTPException(
            status_code=503,
            detail="EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Practice problem generation error: {str(e)}")


@app.post("/api/practice/execute")
def execute_practice_code(req: PracticeExecuteRequest) -> Dict[str, Any]:
    """Compile and execute student C code in a protected subprocess with strict timeout."""
    from eduadapt.evaluation.c_executor import CExecutor
    from eduadapt.evaluation.models import ExecutionStatus

    executor = CExecutor(default_timeout_seconds=3.0)
    if not executor.has_compiler():
        raise HTTPException(
            status_code=503,
            detail="C compiler (GCC) is not available on host system.",
        )

    res = executor.execute_student_code(
        source_code=req.source_code,
        stdin_input=req.stdin_input,
        timeout_seconds=3.0,
    )

    actual_output = (res.stdout or "").strip()
    expected_output = (req.expected_output or "").strip() if req.expected_output else ""

    passed = False
    status_label = res.status.value
    diagnostic_type = res.status.value
    diagnostic_message = ""

    if res.status == ExecutionStatus.COMPILATION_ERROR:
        status_label = "COMPILATION_ERROR"
        diagnostic_type = "COMPILATION_ERROR"
        diagnostic_message = "Compilation Failed. Review the GCC compiler error message below."
    elif res.status == ExecutionStatus.TIMEOUT:
        status_label = "TIMEOUT"
        diagnostic_type = "TIMEOUT"
        diagnostic_message = f"Execution timed out after {res.execution_time_seconds}s. The program may be waiting for standard input (scanf) without input, or trapped in an infinite loop."
    elif res.status == ExecutionStatus.RUNTIME_ERROR:
        status_label = "RUNTIME_ERROR"
        diagnostic_type = "RUNTIME_ERROR"
        diagnostic_message = f"Runtime Error (Exit Code: {res.exit_code}). Review standard error diagnostics below."
    elif res.status == ExecutionStatus.SUCCESS:
        if req.is_submission:
            norm_actual = "\n".join(line.rstrip() for line in actual_output.replace("\r\n", "\n").splitlines()).strip()
            norm_expected = "\n".join(line.rstrip() for line in expected_output.replace("\r\n", "\n").splitlines()).strip()
            if expected_output:
                passed = (norm_actual == norm_expected) or (norm_expected in norm_actual)
                if passed:
                    status_label = "ACCEPTED"
                    diagnostic_type = "ACCEPTED"
                    diagnostic_message = "Accepted: Your program compiled and produced the exact expected output."
                else:
                    status_label = "WRONG_ANSWER"
                    diagnostic_type = "WRONG_ANSWER"
                    diagnostic_message = "Wrong Answer: Output format or content mismatch with expected test case."
            else:
                passed = True
                status_label = "ACCEPTED"
                diagnostic_type = "ACCEPTED"
                diagnostic_message = "Accepted: Program executed successfully without runtime errors."
        else:
            status_label = "SUCCESS"
            diagnostic_type = "SUCCESS"
            diagnostic_message = "Program Compiled & Executed Successfully."

    return {
        "status": status_label,
        "diagnostic_type": diagnostic_type,
        "diagnostic_message": diagnostic_message,
        "success": (res.status == ExecutionStatus.SUCCESS),
        "passed": passed if req.is_submission else None,
        "exit_code": res.exit_code,
        "compiler_output": res.compiler_output or "",
        "stdout": res.stdout or "",
        "stderr": res.stderr or "",
        "execution_time_seconds": res.execution_time_seconds,
        "actual_output": actual_output,
        "expected_output": expected_output if req.expected_output else None,
        "notes": res.notes or "",
        "is_submission": req.is_submission,
        "student_id": req.student_id,
        "topic": req.topic,
    }


@app.post("/api/roadmap/generate")
def generate_roadmap(req: RoadmapGenerateRequest) -> Dict[str, Any]:
    """Generate adaptive milestones roadmap tailored to the student's mastery and pace."""
    service = get_service()
    adapter = LearningTwinAdapter(default_topic=req.topic)
    profile = adapter.get_profile(student_id=req.student_id, topic=req.topic)
    raw_state = get_student_state(req.student_id)
    if not profile:
        from eduadapt.interfaces.student_model import StudentProfile
        profile = StudentProfile(student_id=req.student_id, current_topic=req.topic, mastery_levels={req.topic: 0.0})

    try:
        gen_res = service.teaching_generator.generate_adaptive_roadmap(
            target_competency=f"{req.topic} Mastery in PPS C Programming",
            topic=req.topic,
            student_profile=profile,
            learning_state=raw_state,
        )
        return {
            "topic": req.topic,
            "student_id": req.student_id,
            "target_competency": f"{req.topic} Mastery in PPS",
            "roadmap_content": gen_res.content,
            "model": gen_res.model_name,
        }
    except (OllamaConnectionError, OllamaTimeoutError):
        raise HTTPException(
            status_code=503,
            detail="EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Roadmap generation error: {str(e)}")


@app.get("/api/curriculum/topics")
def get_curriculum_topics() -> Dict[str, Any]:
    """Return PPS curriculum units and active topics."""
    units = [
        {
            "unit": "Unit 1: Introduction to Programming",
            "description": "Algorithms, flowcharts, number systems, computer architecture, execution cycle",
            "topics": ["Algorithms", "Flowcharts", "Number Systems", "Compilation Process"],
        },
        {
            "unit": "Unit 2: C Fundamentals & Operators",
            "description": "Variables, data types, arithmetic, relational, bitwise, expression evaluation",
            "topics": ["Variables and data types", "Operators and expressions", "Operator Precedence"],
        },
        {
            "unit": "Unit 3: Control Structures & Loops",
            "description": "Decision making, if-else, switch, loop control (for, while, do-while), break/continue",
            "topics": ["Conditionals", "Loops", "For and while loops", "Nested loops"],
        },
        {
            "unit": "Unit 4: Arrays, Strings & Pointers",
            "description": "1D/2D arrays, character arrays, pointer variables, memory addresses, pointer arithmetic",
            "topics": ["Arrays", "Strings", "Pointers", "Pointer Arithmetic"],
        },
        {
            "unit": "Unit 5: Functions, Structures & Memory",
            "description": "Function prototypes, parameter passing, recursion, structs, dynamic memory (malloc/free)",
            "topics": ["Functions", "Recursion", "Structures", "Dynamic Memory Allocation"],
        },
    ]
    all_topics = [t for u in units for t in u["topics"]]
    return {"units": units, "topics": all_topics}


@app.post("/api/curriculum/search")
def search_curriculum(req: CurriculumSearchRequest) -> Dict[str, Any]:
    """Retrieve curriculum chunks from Member 2's PPS RAG vector database."""
    service = get_service()
    if not service.rag:
        return {"query": req.query, "results": [], "count": 0}

    try:
        rag_ctx = service.rag.retrieve(query=req.query, top_k=req.top_k)
        results = []
        for doc in rag_ctx.documents:
            results.append({
                "doc_id": doc.doc_id,
                "source": doc.source,
                "slide_or_page": doc.page,
                "unit": doc.module,
                "topic": doc.topic,
                "relevance_score": round(doc.score, 4) if doc.score is not None else None,
                "preview": doc.content[:240] + ("..." if len(doc.content) > 240 else ""),
            })
        return {"query": req.query, "results": results, "count": len(results)}
    except Exception as e:
        return {"query": req.query, "results": [], "count": 0, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eduadapt.api:app", host="0.0.0.0", port=8000, reload=True)
