"""CLI script to execute the 20-question PPS Teaching Evaluation Framework.

Usage:
    # Run full 20-question evaluation against Ollama Mistral 7B:
    python scripts/run_pps_evaluation.py --provider ollama --model mistral:7b

    # Run quick mock test:
    python scripts/run_pps_evaluation.py --provider mock

    # Run specific questions:
    python scripts/run_pps_evaluation.py --provider ollama --questions pps_10,pps_11
"""

import argparse
import logging
from pathlib import Path
import sys
import time

# Ensure src/ is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from eduadapt.evaluation.benchmark import load_benchmark, validate_benchmark
from eduadapt.evaluation.c_executor import CExecutor, discover_c_compiler
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.evaluation.runner import PPSEvaluationRunner
from eduadapt.inference.base import MockLLMClient
from eduadapt.inference.ollama import OllamaLLMClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the EduAdapt PPS Teaching Evaluation Framework."
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "mock"],
        default="ollama",
        help="Inference provider to evaluate (default: ollama).",
    )
    parser.add_argument(
        "--model",
        default="mistral:7b",
        help="Model name (default: mistral:7b).",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Base URL for Ollama service (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Per-request inference timeout in seconds (default: 180.0).",
    )
    parser.add_argument(
        "--questions",
        type=str,
        default=None,
        help="Comma-separated question IDs to evaluate (e.g. pps_01,pps_11). Defaults to all 20.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/evaluation_results_mistral7b.json",
        help="Path to save evaluation JSON results (default: data/evaluation_results_mistral7b.json).",
    )
    parser.add_argument(
        "--compiler",
        type=str,
        default=None,
        help="Optional path to C compiler executable (default: auto-discover GCC).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print("=" * 75)
    print("  EduAdapt: Programming for Problem Solving (PPS) Evaluation Runner")
    print("=" * 75)
    print(f"  Provider       : {args.provider}")
    print(f"  Model          : {args.model}")
    print(f"  Output Path    : {args.output}")

    # Discover and report compiler
    c_compiler = discover_c_compiler(args.compiler)
    if c_compiler:
        print(f"  Compiler       : {c_compiler} (for trusted reference code only)")
    else:
        print("  Compiler       : None discovered (trusted reference runs will be skipped)")
    print("  LLM Safety     : LLM-generated code marked NOT_EXECUTED_UNTRUSTED (never executed)")
    print("=" * 75)

    # Initialize LLM Client
    if args.provider == "ollama":
        llm_client = OllamaLLMClient(
            base_url=args.ollama_url,
            model_name=args.model,
            temperature=0.7,
            max_tokens=1024,
            timeout=args.timeout,
        )
    else:
        llm_client = MockLLMClient(model_name=args.model or "mock-pps-model")

    c_executor = CExecutor(compiler_path=args.compiler)
    runner = PPSEvaluationRunner(llm_client=llm_client, c_executor=c_executor)

    # Load benchmark items
    benchmark_path = BASE_DIR / "data" / "benchmark" / "pps_benchmark_20.json"
    items = load_benchmark(benchmark_path)
    validate_benchmark(items)

    if args.questions:
        selected_ids = {q.strip() for q in args.questions.split(",")}
        items = [item for item in items if item.id in selected_ids]
        if not items:
            print(f"Error: No matching benchmark items found for IDs: {args.questions}")
            sys.exit(1)
        print(f"  Selected items : {len(items)} questions ({', '.join(q.id for q in items)})")
    else:
        print(f"  Benchmark      : All {len(items)} questions loaded successfully.")

    print("\nStarting evaluation execution...\n")

    def on_progress(current, total, result_item):
        cov = result_item.automated_indicators.concept_coverage
        reg = result_item.automated_indicators.while_loop_regression
        ref = result_item.automated_indicators.trusted_reference_execution

        reg_str = ""
        if reg:
            reg_str = " | RegCheck: PASSED" if reg.passed else f" | RegCheck: FAILED ({reg.detected_error_phrase})"

        ref_str = ""
        if ref:
            ref_str = f" | RefCode: {ref.status.value}"

        print(
            f"[{current:02d}/{total:02d}] {result_item.benchmark_id} ({result_item.topic}) "
            f"-> Latency: {result_item.latency_seconds:.2f}s | "
            f"Tokens: {result_item.completion_tokens or 0} | "
            f"Coverage: {cov.coverage_ratio * 100:.0f}%"
            f"{reg_str}{ref_str}"
        )

    t_start = time.time()
    summary = runner.run_benchmark(benchmark_items=items, progress_callback=on_progress)
    total_time = time.time() - t_start

    # Save results
    output_path = BASE_DIR / args.output
    runner.save_results(summary, output_path)

    # Print summary table
    print("\n" + "=" * 75)
    print("  EVALUATION BENCHMARK SUMMARY")
    print("=" * 75)
    print(f"  Total Questions Evaluated       : {summary.total_questions}")
    print(f"  Total Execution Time            : {total_time:.2f}s")
    print(f"  Mean Latency per Item           : {summary.mean_latency_seconds:.2f}s")
    print(f"  Total Prompt Tokens             : {summary.total_prompt_tokens}")
    print(f"  Total Completion Tokens         : {summary.total_completion_tokens}")
    print(f"  Mean Concept Coverage Ratio     : {summary.mean_concept_coverage_ratio * 100:.1f}%")
    print(f"  Trusted Reference Runs Passed   : {summary.trusted_reference_passed}/{summary.trusted_reference_runs}")
    print(f"  While-Loop Regressions Detected : {summary.while_loop_regressions_detected}")
    print(f"  LLM Code Host Safety Status     : ALL EXTRACTED CODE MARKED NOT_EXECUTED_UNTRUSTED")
    print(f"  Manual Review Status            : Placeholders created; awaiting expert human review")
    print(f"  Full Results Saved To           : {output_path}")
    print("=" * 75)


if __name__ == "__main__":
    main()
