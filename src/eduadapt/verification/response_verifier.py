"""Response and Grounding Verification Module (Member 4 Contribution).

Performs deterministic, non-agentic verification signals over generated teaching content:
1. Response presence and non-emptiness.
2. Curriculum context availability and source tracking.
3. Grounding / lexical and concept overlap against retrieved PPS slides.
4. C code detection, extraction, and host safety enforcement (NOT_EXECUTED_UNTRUSTED).
5. Integration with while-loop regression checker.

Pedagogical and safety note:
This module computes deterministic verification signals and grounding coverage.
It does NOT claim mathematical or educational correctness proofs based solely on keyword overlap.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional, Set

from eduadapt.evaluation.c_executor import extract_c_code
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.evaluation.regression import check_while_loop_explanation


# Minimal stop words for computing meaningful curriculum term overlap
COMMON_STOP_WORDS = {
    "the", "and", "or", "to", "in", "a", "an", "is", "are", "was", "were", "of",
    "that", "this", "it", "for", "on", "with", "as", "by", "at", "from", "be",
    "have", "has", "had", "can", "could", "will", "would", "should", "shall",
    "which", "who", "whom", "its", "their", "our", "your", "my", "if", "then",
    "else", "when", "into", "also", "about", "above", "after", "before", "between",
}


def tokenize_text(text: str) -> Set[str]:
    """Extract lowercased alphanumeric words excluding generic stop words."""
    words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text.lower())
    return {w for w in words if len(w) > 2 and w not in COMMON_STOP_WORDS}


@dataclass
class GroundingVerificationResult:
    """Encapsulates response grounding and safety verification signals."""

    generation_completed: bool
    curriculum_context_available: bool
    retrieved_sources_count: int
    matched_curriculum_terms_count: int
    grounding_ratio: float
    grounding_status: str
    code_detected: bool
    extracted_code_lines: int
    code_execution_status: str
    safety_status: str
    regression_status: str
    overall_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation_completed": self.generation_completed,
            "curriculum_context_available": self.curriculum_context_available,
            "retrieved_sources_count": self.retrieved_sources_count,
            "matched_curriculum_terms_count": self.matched_curriculum_terms_count,
            "grounding_ratio": round(self.grounding_ratio, 3),
            "grounding_status": self.grounding_status,
            "code_detected": self.code_detected,
            "extracted_code_lines": self.extracted_code_lines,
            "code_execution": self.code_execution_status,
            "safety_status": self.safety_status,
            "regression_check": self.regression_status,
            "overall_status": self.overall_status,
        }


class ResponseVerifier:
    """Deterministic response and curriculum grounding verifier."""

    @staticmethod
    def verify_response(
        response_text: str,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        topic: str = "",
    ) -> GroundingVerificationResult:
        """Run verification checks on generated pedagogical response.

        Args:
            response_text: The LLM-generated teaching content.
            retrieved_chunks: List of retrieved RAG chunk metadata/content dictionaries.
            topic: Target PPS topic.

        Returns:
            GroundingVerificationResult containing verification signals.
        """
        # 1. Non-empty check
        has_content = bool(response_text and response_text.strip())

        # 2. Curriculum context existence
        chunks = retrieved_chunks or []
        context_available = len(chunks) > 0

        # 3. Grounding / concept overlap check
        curriculum_text = " ".join(
            (c.get("preview") or "") + " " + (c.get("topic") or "") + " " + (c.get("unit_or_module") or "")
            for c in chunks
        )
        if topic:
            curriculum_text += f" {topic}"

        curriculum_tokens = tokenize_text(curriculum_text)
        response_tokens = tokenize_text(response_text)

        matched_tokens = curriculum_tokens.intersection(response_tokens)
        matched_count = len(matched_tokens)

        if curriculum_tokens:
            grounding_ratio = matched_count / len(curriculum_tokens)
        else:
            grounding_ratio = 1.0 if has_content else 0.0

        if not context_available:
            grounding_status = "Unverified (no curriculum context supplied)"
        elif matched_count >= 5 or (curriculum_tokens and grounding_ratio >= 0.15):
            grounding_status = "Verified: grounded in retrieved PPS curriculum terminology"
        else:
            grounding_status = "Weak grounding: limited overlap with retrieved PPS terminology"

        # 4. C code detection and host safety enforcement
        extracted_code = extract_c_code(response_text)
        code_detected = bool(extracted_code)
        extracted_lines = len(extracted_code.splitlines()) if extracted_code else 0

        code_exec_status = ExecutionStatus.NOT_EXECUTED_UNTRUSTED.value
        safety_status = "Enforced: untrusted LLM code is NOT executed on host machine"

        # 5. Regression check
        reg_check = check_while_loop_explanation(response_text)
        regression_status = "Passed" if reg_check.passed else f"Failed: {reg_check.explanation}"

        # 6. Overall deterministic signal
        if has_content and reg_check.passed:
            overall_status = "VERIFIED_SAFE"
        elif not has_content:
            overall_status = "FAILED_EMPTY_RESPONSE"
        else:
            overall_status = "FLAGGED_REGRESSION"

        return GroundingVerificationResult(
            generation_completed=has_content,
            curriculum_context_available=context_available,
            retrieved_sources_count=len(chunks),
            matched_curriculum_terms_count=matched_count,
            grounding_ratio=grounding_ratio,
            grounding_status=grounding_status,
            code_detected=code_detected,
            extracted_code_lines=extracted_lines,
            code_execution_status=code_exec_status,
            safety_status=safety_status,
            regression_status=regression_status,
            overall_status=overall_status,
        )
