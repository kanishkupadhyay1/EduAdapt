"""Evaluation framework for Programming for Problem Solving (PPS)."""

from eduadapt.evaluation.benchmark import load_benchmark, validate_benchmark
from eduadapt.evaluation.c_executor import CExecutor, discover_c_compiler, extract_c_code
from eduadapt.evaluation.models import (
    BenchmarkItem,
    CodeExecutionResult,
    EvaluationResultItem,
    EvaluationRunSummary,
    ExecutionStatus,
    ManualReviewRating,
    StudentProfileContext,
)
from eduadapt.evaluation.regression import check_while_loop_explanation
from eduadapt.evaluation.runner import PPSEvaluationRunner, compute_concept_coverage

__all__ = [
    "BenchmarkItem",
    "CExecutor",
    "CodeExecutionResult",
    "EvaluationResultItem",
    "EvaluationRunSummary",
    "ExecutionStatus",
    "ManualReviewRating",
    "PPSEvaluationRunner",
    "StudentProfileContext",
    "check_while_loop_explanation",
    "compute_concept_coverage",
    "discover_c_compiler",
    "extract_c_code",
    "load_benchmark",
    "validate_benchmark",
]
