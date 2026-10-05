"""Evaluation Runner for the Programming for Problem Solving (PPS) curriculum.

Orchestrates live model evaluations against the 20-question PPS benchmark.
Tracks latency, token usage, concept-coverage indicators, while-loop regression detection,
and executes trusted reference programs with safety boundaries.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Callable, List, Optional

from eduadapt.evaluation.benchmark import load_benchmark, validate_benchmark
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import (
    AutomatedIndicators,
    BenchmarkItem,
    ConceptCoverageIndicator,
    EvaluationResultItem,
    EvaluationRunSummary,
    ExecutionStatus,
    ManualReviewRating,
    WhileLoopRegressionCheck,
)
from eduadapt.evaluation.regression import check_while_loop_explanation
from eduadapt.inference.base import BaseLLMClient
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.generator import PersonalizedContentGenerator

logger = logging.getLogger("eduadapt.evaluation.runner")


def compute_concept_coverage(
    generated_text: str, keywords: List[str]
) -> ConceptCoverageIndicator:
    """Compute automated keyword presence indicators.

    IMPORTANT: This metric indicates keyword coverage only; it does NOT constitute
    proof of conceptual correctness.
    """
    if not keywords:
        return ConceptCoverageIndicator(
            total_keywords=0,
            matched_keywords=[],
            missing_keywords=[],
            coverage_ratio=1.0,
        )

    text_lower = generated_text.lower()
    matched = []
    missing = []

    for kw in keywords:
        if kw.lower() in text_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    ratio = round(len(matched) / len(keywords), 3)
    return ConceptCoverageIndicator(
        total_keywords=len(keywords),
        matched_keywords=matched,
        missing_keywords=missing,
        coverage_ratio=ratio,
    )


class PPSEvaluationRunner:
    """Orchestrates non-agentic evaluation of PPS instructional explanations."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        c_executor: Optional[CExecutor] = None,
        prompt_manager: Optional[PromptManager] = None,
        teaching_service: Optional[PersonalizedContentGenerator] = None,
    ) -> None:
        self.llm_client = llm_client
        self.c_executor = c_executor or CExecutor()
        self.prompt_manager = prompt_manager or PromptManager()
        self.teaching_service = teaching_service or PersonalizedContentGenerator(
            llm_client=self.llm_client, prompt_manager=self.prompt_manager
        )

    def evaluate_item(self, item: BenchmarkItem) -> EvaluationResultItem:
        """Run evaluation for a single benchmark item."""
        # Build StudentProfile representation from benchmark item
        student_profile = StudentProfile(
            student_id=item.student_profile.student_id,
            current_topic=item.topic,
            mastery_levels=item.student_profile.mastery_levels,
            preferred_pace=item.student_profile.preferred_pace,
            common_misconceptions=item.student_profile.common_misconceptions,
        )

        additional_context = (
            f"Specific Question: {item.question}\n"
            f"Expected C Standards Context: {item.c_standard_assumptions}"
        )

        # 1. Run model inference and track latency
        t0 = time.time()
        gen_result = self.teaching_service.generate_for_student(
            topic=item.topic,
            student_profile=student_profile,
            preferred_response_format=item.student_profile.preferred_response_format,
            performance_history=item.student_profile.performance_history,
            additional_context=additional_context,
        )
        latency = round(time.time() - t0, 3)

        generated_text = gen_result.content

        # 2. Automated concept-coverage indicator (keyword presence)
        coverage_indicator = compute_concept_coverage(
            generated_text=generated_text,
            keywords=item.concept_coverage_keywords,
        )

        # 3. SAFETY RULE: Handle LLM-generated code
        # LLM-generated code is NEVER executed on the host machine.
        # It is extracted and saved with status ExecutionStatus.NOT_EXECUTED_UNTRUSTED.
        llm_code_result = self.c_executor.handle_untrusted_llm_code(generated_text)

        # 4. Compile and execute TRUSTED reference code (if provided)
        trusted_ref_result = None
        if item.trusted_reference_code:
            trusted_ref_result = self.c_executor.execute_trusted_reference(
                source_code=item.trusted_reference_code
            )

        # 5. Targeted regression check (for while-loop termination or loop items)
        regression_check = None
        if "while" in item.topic.lower() or "while" in item.question.lower() or item.id == "pps_11":
            regression_check = check_while_loop_explanation(generated_text)

        automated_indicators = AutomatedIndicators(
            concept_coverage=coverage_indicator,
            extracted_c_code=llm_code_result.source_code if llm_code_result.source_code else None,
            llm_code_execution_status=llm_code_result.status,
            trusted_reference_execution=trusted_ref_result,
            while_loop_regression=regression_check,
        )

        prompt_tokens = gen_result.prompt_tokens
        completion_tokens = gen_result.completion_tokens
        total_tokens = (
            (prompt_tokens or 0) + (completion_tokens or 0)
            if (prompt_tokens is not None and completion_tokens is not None)
            else None
        )

        return EvaluationResultItem(
            benchmark_id=item.id,
            topic=item.topic,
            difficulty=item.difficulty,
            student_mastery_level=item.student_mastery_level,
            question=item.question,
            generated_content=generated_text,
            latency_seconds=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_name=gen_result.model_name,
            automated_indicators=automated_indicators,
            manual_review=ManualReviewRating(),
        )

    def run_benchmark(
        self,
        benchmark_items: Optional[List[BenchmarkItem]] = None,
        progress_callback: Optional[Callable[[int, int, EvaluationResultItem], None]] = None,
    ) -> EvaluationRunSummary:
        """Run evaluation over the complete benchmark suite."""
        items = benchmark_items or load_benchmark()
        validate_benchmark(items)

        total_questions = len(items)
        results: List[EvaluationResultItem] = []
        latencies: List[float] = []
        coverage_ratios: List[float] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        trusted_runs = 0
        trusted_passed = 0
        regressions_detected = 0

        for idx, item in enumerate(items, start=1):
            logger.info("Evaluating [%d/%d] %s: %s", idx, total_questions, item.id, item.topic)
            res_item = self.evaluate_item(item)
            results.append(res_item)

            latencies.append(res_item.latency_seconds)
            coverage_ratios.append(res_item.automated_indicators.concept_coverage.coverage_ratio)
            if res_item.prompt_tokens:
                total_prompt_tokens += res_item.prompt_tokens
            if res_item.completion_tokens:
                total_completion_tokens += res_item.completion_tokens

            ref_exec = res_item.automated_indicators.trusted_reference_execution
            if ref_exec and ref_exec.status != ExecutionStatus.NO_CODE:
                trusted_runs += 1
                if ref_exec.status == ExecutionStatus.SUCCESS:
                    trusted_passed += 1

            reg_check = res_item.automated_indicators.while_loop_regression
            if reg_check and not reg_check.passed:
                regressions_detected += 1

            if progress_callback:
                progress_callback(idx, total_questions, res_item)

        mean_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        mean_coverage = (
            round(sum(coverage_ratios) / len(coverage_ratios), 3) if coverage_ratios else 0.0
        )

        return EvaluationRunSummary(
            model_name=getattr(self.llm_client, "model_name", "unknown"),
            inference_provider=type(self.llm_client).__name__,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_questions=total_questions,
            successful_inferences=len(results),
            failed_inferences=0,
            mean_latency_seconds=mean_latency,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            mean_concept_coverage_ratio=mean_coverage,
            compiler_detected=self.c_executor.compiler_path,
            trusted_reference_runs=trusted_runs,
            trusted_reference_passed=trusted_passed,
            while_loop_regressions_detected=regressions_detected,
            results=results,
        )

    @staticmethod
    def save_results(summary: EvaluationRunSummary, output_path: Path) -> None:
        """Persist evaluation summary and detailed items to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))
        logger.info("Saved evaluation results to %s", output_path)
