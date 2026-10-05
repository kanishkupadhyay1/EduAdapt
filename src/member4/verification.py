"""Response verification interfaces for the EduAdapt Member 4 module."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VerificationResult:
    """Result returned by the response verification layer."""

    verified: bool
    grounded: bool
    issues: List[str] = field(default_factory=list)
    message: str = ""


class ResponseVerifier:
    """Verify generated teaching responses independently of generation."""

    def verify(
        self,
        generated_response: str,
        source_context: Optional[str] = None,
    ) -> VerificationResult:
        """
        Perform basic response and grounding checks.

        This is the initial interface implementation. More advanced
        grounding checks can be added later without changing the interface.
        """

        issues = []

        if not generated_response or not generated_response.strip():
            issues.append("Generated response is empty.")

        if source_context is not None and not source_context.strip():
            issues.append("Source context is empty.")

        if issues:
            return VerificationResult(
                verified=False,
                grounded=False,
                issues=issues,
                message="Response failed verification.",
            )

        return VerificationResult(
            verified=True,
            grounded=source_context is not None,
            issues=[],
            message="Response passed basic verification.",
        )