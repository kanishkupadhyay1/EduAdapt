"""Learning roadmap generator for Programming for Problem Solving (PPS).

Constructs sequence of milestones based on student target competency and mastery.
Pure generative prompt-driven module; no autonomous agent loop.
"""

from typing import Optional
from eduadapt.inference.base import BaseLLMClient, GenerationResult
from eduadapt.prompts.templates import PromptManager


class RoadmapGenerator:
    """Generates customized topic learning roadmaps."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager or PromptManager()

    def generate_roadmap(
        self,
        target_competency: str,
        current_mastery: str = "Beginner",
    ) -> GenerationResult:
        """Generate a learning roadmap from the current mastery to the target competency."""
        template = self.prompt_manager.get("roadmap_generation")
        prompt = template.render(
            target_competency=target_competency,
            current_mastery=current_mastery,
        )
        return self.llm_client.generate(prompt=prompt)
