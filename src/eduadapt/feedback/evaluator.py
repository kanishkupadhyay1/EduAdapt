"""Feedback and hint generation module for student problem solving.

Processes code submissions and produces constructive guidance without running agents.
"""

from typing import Optional
from eduadapt.inference.base import BaseLLMClient, GenerationResult
from eduadapt.prompts.templates import PromptManager


class FeedbackGenerator:
    """Generates pedagogical feedback and hints for student code submissions."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager or PromptManager()

    def generate_feedback(
        self,
        problem_description: str,
        student_code: str,
    ) -> GenerationResult:
        """Generate constructive feedback on a student's solution."""
        template = self.prompt_manager.get("feedback_generation")
        prompt = template.render(
            problem_description=problem_description,
            student_code=student_code,
        )
        return self.llm_client.generate(prompt=prompt)
