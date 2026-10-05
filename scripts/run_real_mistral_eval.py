"""Execution script for running real Mistral:7b inference via Ollama.

Tests four distinct pedagogical PPS scenarios:
1. C variables
2. Beginner for loops (using beginner learner profile)
3. Advanced nested loops (using advanced learner profile)
4. Simple C programming examples (variable swap / basic logic)

Saves actual responses, prompt tokens, completion tokens, and timing to data/real_model_responses.json.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.generator import PersonalizedContentGenerator


def run_evaluation():
    print("=" * 60)
    print("Connecting to local Ollama (model: mistral:7b, timeout: 180s)...")
    print("=" * 60)

    client = OllamaLLMClient(
        base_url="http://localhost:11434",
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=1024,
        timeout=180.0,
    )
    prompt_manager = PromptManager()
    teaching_service = PersonalizedContentGenerator(
        llm_client=client, prompt_manager=prompt_manager
    )

    results = []

    # Scenario 1: C Variables
    print("\n[1/4] Running inference for: C Variables...")
    t0 = time.time()
    res_1 = teaching_service.generate_explanation(
        topic="Variables and Data Types in C",
        learning_preference="conceptual explanation with variable memory diagram and code examples",
        context="Introductory C programming for first-year engineering students (PPS)",
    )
    elapsed_1 = time.time() - t0
    print(f"-> Completed in {elapsed_1:.2f}s | Prompt tokens: {res_1.prompt_tokens} | Completion tokens: {res_1.completion_tokens}")
    results.append({
        "scenario_id": "c_variables",
        "topic": "Variables and Data Types in C",
        "elapsed_seconds": round(elapsed_1, 2),
        "prompt_tokens": res_1.prompt_tokens,
        "completion_tokens": res_1.completion_tokens,
        "model_name": res_1.model_name,
        "content": res_1.content,
    })

    # Scenario 2: Beginner For Loops
    print("\n[2/4] Running inference for: Beginner For Loops...")
    beginner_profile = StudentProfile(
        student_id="std_beginner_loops",
        current_topic="For Loops",
        mastery_levels={"Variables": 0.7, "Conditional Statements": 0.65, "Loops": 0.25},
        learning_style="guided_scaffolded",
        preferred_pace="slow",
        common_misconceptions=[
            "Thinking loop update condition runs before the loop body executes",
            "Off-by-one errors with <= versus < operators",
        ],
    )
    t0 = time.time()
    res_2 = teaching_service.generate_for_student(
        topic="For Loops in C",
        student_profile=beginner_profile,
        preferred_response_format="step-by-step execution trace table with annotated small C code",
        performance_history="Struggled on practice quiz 1 with iteration count; confused about initialization vs condition",
        additional_context="Focus on how i++ works and exact order of execution (Init -> Condition -> Body -> Update)",
    )
    elapsed_2 = time.time() - t0
    print(f"-> Completed in {elapsed_2:.2f}s | Prompt tokens: {res_2.prompt_tokens} | Completion tokens: {res_2.completion_tokens}")
    results.append({
        "scenario_id": "beginner_for_loops",
        "topic": "For Loops in C",
        "student_profile": beginner_profile.model_dump(),
        "elapsed_seconds": round(elapsed_2, 2),
        "prompt_tokens": res_2.prompt_tokens,
        "completion_tokens": res_2.completion_tokens,
        "model_name": res_2.model_name,
        "content": res_2.content,
    })

    # Scenario 3: Advanced Nested Loops
    print("\n[3/4] Running inference for: Advanced Nested Loops...")
    advanced_profile = StudentProfile(
        student_id="std_advanced_loops",
        current_topic="Nested Loops",
        mastery_levels={"Loops": 0.95, "Nested Loops": 0.85, "Arrays": 0.9},
        learning_style="technical_rigorous",
        preferred_pace="fast",
        common_misconceptions=[],
    )
    t0 = time.time()
    res_3 = teaching_service.generate_for_student(
        topic="Nested Loops in C",
        student_profile=advanced_profile,
        preferred_response_format="rigorous technical explanation with 2D array traversal, row-major memory order, and nested iteration complexity analysis",
        performance_history="Consistently achieves 100% on basic iteration questions; ready for multi-dimensional structures",
        additional_context="Highlight time complexity O(N*M) and row-major cache locality in 2D array traversal",
    )
    elapsed_3 = time.time() - t0
    print(f"-> Completed in {elapsed_3:.2f}s | Prompt tokens: {res_3.prompt_tokens} | Completion tokens: {res_3.completion_tokens}")
    results.append({
        "scenario_id": "advanced_nested_loops",
        "topic": "Nested Loops in C",
        "student_profile": advanced_profile.model_dump(),
        "elapsed_seconds": round(elapsed_3, 2),
        "prompt_tokens": res_3.prompt_tokens,
        "completion_tokens": res_3.completion_tokens,
        "model_name": res_3.model_name,
        "content": res_3.content,
    })

    # Scenario 4: Simple C Programming Examples
    print("\n[4/4] Running inference for: Simple C Programming Examples...")
    t0 = time.time()
    res_4 = client.generate(
        prompt=(
            "You are a PPS C programming tutor. Provide three simple, essential C programming examples "
            "for first-year engineers:\n"
            "1. Swapping two integers using a third temporary variable.\n"
            "2. Finding the largest of two numbers using an if-else statement.\n"
            "3. Calculating the sum of first N natural numbers using a while loop.\n\n"
            "For each example, provide clean, fully-formed C code with comments and a concise explanation."
        ),
        system_instruction="You are an expert tutor for Programming for Problem Solving (PPS).",
        temperature=0.6,
        max_tokens=1024,
    )
    elapsed_4 = time.time() - t0
    print(f"-> Completed in {elapsed_4:.2f}s | Prompt tokens: {res_4.prompt_tokens} | Completion tokens: {res_4.completion_tokens}")
    results.append({
        "scenario_id": "simple_c_programming_examples",
        "topic": "Simple C Programming Examples",
        "elapsed_seconds": round(elapsed_4, 2),
        "prompt_tokens": res_4.prompt_tokens,
        "completion_tokens": res_4.completion_tokens,
        "model_name": res_4.model_name,
        "content": res_4.content,
    })

    # Save to data/real_model_responses.json
    output_path = BASE_DIR / "data" / "real_model_responses.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": "mistral:7b",
                "inference_provider": "ollama",
                "endpoint": "http://localhost:11434",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_scenarios": len(results),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\nAll 4 real model inferences completed successfully and saved to: {output_path}")


if __name__ == "__main__":
    run_evaluation()
