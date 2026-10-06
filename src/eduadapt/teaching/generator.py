"""Personalized content generator for PPS course.

Owns personalized explanations and learning materials generation via direct LLM inference.
Does not implement agentic loops or autonomous workflows.
"""

from typing import Optional
from eduadapt.inference.base import BaseLLMClient, GenerationResult
from eduadapt.interfaces.rag import RAGInterface
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager


class PersonalizedContentGenerator:
    """Generates personalized learning content adapted to student needs."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_manager: Optional[PromptManager] = None,
        rag: Optional[RAGInterface] = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager or PromptManager()
        self.rag = rag

    def generate_explanation(
        self,
        topic: str,
        learning_preference: str = "visual and code-focused",
        context: str = "Introductory level",
    ) -> GenerationResult:
        """Generate a personalized explanation for a PPS topic."""
        template = self.prompt_manager.get("teaching_explanation")
        prompt = template.render(
            topic=topic,
            learning_preference=learning_preference,
            context=context,
        )
        return self.llm_client.generate(prompt=prompt)

    def generate_for_student(
        self,
        topic: str,
        student_profile: StudentProfile,
        preferred_response_format: str = "concise explanation with commented C code and step-by-step trace",
        performance_history: Optional[str] = None,
        additional_context: str = "",
    ) -> GenerationResult:
        """Generate a personalized explanation tailored to a student's mastery profile.

        Pedagogical grounding:
        Adapts instruction according to student mastery state, performance history,
        known misconceptions, and preferred response format, avoiding fixed learning-style assumptions.
        """
        mastery_score = student_profile.mastery_levels.get(topic, 0.0)
        if mastery_score >= 0.7:
            mastery_level = (
                f"Advanced ({mastery_score:.2f}) - focus on nuances, edge cases, memory layout, "
                "and idiomatic efficiency"
            )
        elif mastery_score >= 0.4:
            mastery_level = (
                f"Intermediate ({mastery_score:.2f}) - reinforce core mechanics and syntax applications"
            )
        else:
            mastery_level = (
                f"Beginner ({mastery_score:.2f}) - provide intuitive foundational breakdown, "
                "simple analogies, and guided walkthrough"
            )

        misconceptions_str = (
            "; ".join(student_profile.common_misconceptions)
            if student_profile.common_misconceptions
            else "None identified"
        )
        history_str = (
            performance_history
            or f"Pace: {student_profile.preferred_pace}, Current curriculum topic: {student_profile.current_topic}"
        )

        # Retrieve curriculum context via RAG if available
        context_str = additional_context
        if self.rag is not None:
            rag_context = self.rag.retrieve(query=topic, top_k=3)
            formatted_rag = rag_context.format_for_prompt()
            if context_str:
                context_str = f"{formatted_rag}\n\nAdditional Student Context:\n{context_str}"
            else:
                context_str = formatted_rag
        elif not context_str:
            context_str = "Standard PPS curriculum progression"

        try:
            template = self.prompt_manager.get("personalized_teaching")
            prompt = template.render(
                topic=topic,
                mastery_level=mastery_level,
                performance_history=history_str,
                misconceptions=misconceptions_str,
                response_format=preferred_response_format,
                context=context_str,
            )
        except KeyError:
            template = self.prompt_manager.get("teaching_explanation")
            prompt = template.render(
                topic=topic,
                learning_preference=preferred_response_format,
                context=f"Mastery: {mastery_level}. Misconceptions: {misconceptions_str}. {context_str}".strip(),
            )

        return self.llm_client.generate(prompt=prompt)
