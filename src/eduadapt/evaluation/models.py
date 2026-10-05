"""Data models for the PPS Teaching Evaluation Framework.

Strictly separates automated metrics and indicators from manual educational review ratings.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status for C programs."""

    SUCCESS = "SUCCESS"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    TIMEOUT = "TIMEOUT"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    NOT_EXECUTED_UNTRUSTED = "NOT_EXECUTED_UNTRUSTED"
    COMPILER_NOT_AVAILABLE = "COMPILER_NOT_AVAILABLE"
    NO_CODE = "NO_CODE"


class CodeExecutionResult(BaseModel):
    """Result of attempting compilation and execution of C code."""

    status: ExecutionStatus
    is_trusted_reference: bool = False
    source_code: str = ""
    compiler_used: Optional[str] = None
    compiler_output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    execution_time_seconds: float = 0.0
    notes: str = ""


class StudentProfileContext(BaseModel):
    """Personalization profile for a PPS learner.

    Relies on mastery scores, performance history, identified misconceptions,
    and preferred response formats. Does not assume fixed learning-style categories.
    """

    student_id: str
    mastery_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Topic-wise mastery scores between 0.0 and 1.0",
    )
    performance_history: str = ""
    common_misconceptions: List[str] = Field(default_factory=list)
    preferred_response_format: str = ""
    preferred_pace: str = "moderate"


class BenchmarkItem(BaseModel):
    """A single benchmark question in the PPS curriculum."""

    id: str
    topic: str
    difficulty: str  # Beginner, Intermediate, Advanced
    student_mastery_level: float = Field(ge=0.0, le=1.0)
    student_profile: StudentProfileContext
    question: str
    expected_key_concepts: List[str]
    concept_coverage_keywords: List[str]
    reference_answer: str
    trusted_reference_code: Optional[str] = None
    expected_program_output: Optional[str] = None
    common_misconceptions: List[str] = Field(default_factory=list)
    c_standard_assumptions: str = "ISO C99 / C11, standard 32/64-bit platform limits"


class ConceptCoverageIndicator(BaseModel):
    """Automated indicator of keyword and key concept presence in generated text.

    Note: This is an indicator of keyword coverage, NOT a proof of conceptual correctness.
    """

    total_keywords: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    coverage_ratio: float


class WhileLoopRegressionCheck(BaseModel):
    """Targeted regression check for while-loop termination explanation error.

    Error pattern: 'loop continues until i is greater than n+1'
    Correct pattern: 'loop terminates when i reaches n+1 because i <= n becomes false'
    """

    checked: bool
    passed: bool
    detected_error_phrase: Optional[str] = None
    explanation: str = ""


class AutomatedIndicators(BaseModel):
    """Aggregate automated checks and indicators."""

    concept_coverage: ConceptCoverageIndicator
    extracted_c_code: Optional[str] = None
    llm_code_execution_status: ExecutionStatus = ExecutionStatus.NOT_EXECUTED_UNTRUSTED
    trusted_reference_execution: Optional[CodeExecutionResult] = None
    while_loop_regression: Optional[WhileLoopRegressionCheck] = None


class ManualReviewRating(BaseModel):
    """Manual human review rating covering 5 pedagogical dimensions.

    Scale: 1 (Unacceptable/Fatal Error) to 5 (Flawless/Exemplary).
    These fields remain placeholders until an authorized human evaluator reviews the response.
    """

    conceptual_correctness: Optional[int] = Field(
        default=None, ge=1, le=5, description="1-5 rating of technical accuracy under C standards"
    )
    code_correctness: Optional[int] = Field(
        default=None, ge=1, le=5, description="1-5 rating of syntactical and logical validity"
    )
    explanation_clarity: Optional[int] = Field(
        default=None, ge=1, le=5, description="1-5 rating of pedagogical structure and lucidity"
    )
    appropriateness_for_student_mastery: Optional[int] = Field(
        default=None, ge=1, le=5, description="1-5 rating of scaffolding tailored to student mastery"
    )
    misconception_handling: Optional[int] = Field(
        default=None, ge=1, le=5, description="1-5 rating of addressing and preventing misconceptions"
    )
    reviewer_notes: str = ""
    evaluated_by: Optional[str] = None
    is_reviewed: bool = False


class EvaluationResultItem(BaseModel):
    """Complete evaluation record for a single benchmark question."""

    benchmark_id: str
    topic: str
    difficulty: str
    student_mastery_level: float
    question: str
    generated_content: str
    latency_seconds: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_name: str
    automated_indicators: AutomatedIndicators
    manual_review: ManualReviewRating = Field(default_factory=ManualReviewRating)


class EvaluationRunSummary(BaseModel):
    """Summary of an evaluation benchmark run."""

    model_name: str
    inference_provider: str
    timestamp: str
    total_questions: int
    successful_inferences: int
    failed_inferences: int
    mean_latency_seconds: float
    total_prompt_tokens: int
    total_completion_tokens: int
    mean_concept_coverage_ratio: float
    compiler_detected: Optional[str] = None
    trusted_reference_runs: int = 0
    trusted_reference_passed: int = 0
    while_loop_regressions_detected: int = 0
    results: List[EvaluationResultItem] = Field(default_factory=list)
