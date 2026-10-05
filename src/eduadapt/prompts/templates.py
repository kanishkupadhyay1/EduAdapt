"""Prompt template structures for Programming for Problem Solving (PPS).

Templates are parameterized and loaded at runtime without hardcoded syllabi.
"""

from typing import Any, Dict
from pydantic import BaseModel


class PromptTemplate(BaseModel):
    """Reusable prompt template definition."""

    name: str
    template: str
    description: str = ""

    def render(self, **kwargs: Any) -> str:
        """Render template with provided variable values."""
        return self.template.format(**kwargs)


class PromptManager:
    """Manages prompt templates across teaching, feedback, and roadmap generation."""

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        self.register(
            PromptTemplate(
                name="teaching_explanation",
                description="Generates personalized PPS concept explanation.",
                template=(
                    "You are an expert tutor for Programming for Problem Solving (PPS).\n"
                    "Topic: {topic}\n"
                    "Student Learning Preference: {learning_preference}\n"
                    "Context: {context}\n\n"
                    "Explain the concept clearly with relevant C programming examples."
                ),
            )
        )
        self.register(
            PromptTemplate(
                name="personalized_teaching",
                description="Generates personalized PPS concept explanation based on mastery, performance history, misconceptions, and response format.",
                template=(
                    "You are an expert tutor for Programming for Problem Solving (PPS) in C.\n"
                    "Topic: {topic}\n"
                    "Student Mastery Level: {mastery_level}\n"
                    "Performance History: {performance_history}\n"
                    "Common Misconceptions to Address: {misconceptions}\n"
                    "Preferred Response Format: {response_format}\n"
                    "Additional Context: {context}\n\n"
                    "Instructions:\n"
                    "- Tailor cognitive depth and scaffolding to the student's mastery level and performance history.\n"
                    "- Explicitly detect and clarify the noted misconceptions without condescension.\n"
                    "- Present practical, syntactically correct C programming examples matching the requested response format."
                ),
            )
        )
        self.register(
            PromptTemplate(
                name="feedback_generation",
                description="Generates constructive feedback for student solution.",
                template=(
                    "You are a code evaluator for Programming for Problem Solving (PPS).\n"
                    "Problem Description: {problem_description}\n"
                    "Student Submission:\n```c\n{student_code}\n```\n\n"
                    "Provide constructive, step-by-step feedback and hints without giving away the full answer."
                ),
            )
        )
        self.register(
            PromptTemplate(
                name="roadmap_generation",
                description="Generates structured learning roadmap for PPS mastery.",
                template=(
                    "Generate a structured milestone-based study roadmap for Programming for Problem Solving (PPS).\n"
                    "Target Competency: {target_competency}\n"
                    "Current Student Mastery: {current_mastery}\n\n"
                    "Provide ordered milestones and practice milestones."
                ),
            )
        )

    def register(self, template: PromptTemplate) -> None:
        """Register a new template."""
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        """Retrieve a template by name."""
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found.")
        return self._templates[name]
