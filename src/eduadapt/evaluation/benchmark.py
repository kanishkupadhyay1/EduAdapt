"""Benchmark dataset loader and validator for PPS evaluation framework."""

import json
from pathlib import Path
from typing import List, Optional

from eduadapt.evaluation.models import BenchmarkItem

DEFAULT_BENCHMARK_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data"
    / "benchmark"
    / "pps_benchmark_20.json"
)

REQUIRED_TOPICS = {
    "Variables and data types",
    "Operators and expressions",
    "Conditionals",
    "For and while loops",
    "Nested loops",
    "Arrays",
    "Functions",
}


def load_benchmark(file_path: Optional[Path] = None) -> List[BenchmarkItem]:
    """Load and parse the PPS benchmark dataset.

    Args:
        file_path: Optional path to the benchmark JSON file.

    Returns:
        List of validated BenchmarkItem instances.

    Raises:
        FileNotFoundError: If the benchmark file is missing.
        ValueError: If fewer than 20 questions or malformed schema.
    """
    path = file_path or DEFAULT_BENCHMARK_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark dataset not found at '{path}'")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Benchmark file '{path}' must contain a list of questions.")

    items = [BenchmarkItem(**item) for item in data]
    return items


def validate_benchmark(
    items: List[BenchmarkItem], require_full_curriculum: bool = False
) -> None:
    """Validate benchmark completeness, topic coverage, and schema constraints.

    Args:
        items: List of BenchmarkItem objects to validate.
        require_full_curriculum: If True, enforces that exactly 20 questions covering
            all 7 PPS syllabus areas are present.

    Raises:
        ValueError: If any constraint is violated.
    """
    if require_full_curriculum and len(items) != 20:
        raise ValueError(f"Benchmark must contain exactly 20 questions, got {len(items)}")

    seen_ids = set()
    found_topics = set()

    for item in items:
        if item.id in seen_ids:
            raise ValueError(f"Duplicate question id detected: {item.id}")
        seen_ids.add(item.id)
        found_topics.add(item.topic)

        if not item.question.strip():
            raise ValueError(f"Empty question field in item {item.id}")
        if not item.expected_key_concepts:
            raise ValueError(f"No expected key concepts defined for item {item.id}")
        if not item.concept_coverage_keywords:
            raise ValueError(f"No concept coverage keywords defined for item {item.id}")
        if not item.reference_answer.strip():
            raise ValueError(f"No reference answer defined for item {item.id}")
        if not item.common_misconceptions:
            raise ValueError(f"No common misconceptions defined for item {item.id}")
        if not (0.0 <= item.student_mastery_level <= 1.0):
            raise ValueError(
                f"Invalid mastery level {item.student_mastery_level} for item {item.id}"
            )

    if require_full_curriculum:
        missing_topics = REQUIRED_TOPICS - found_topics
        if missing_topics:
            raise ValueError(f"Benchmark is missing required PPS topics: {missing_topics}")
