"""Personalized content generator for PPS course.

Owns personalized explanations and learning materials generation via direct LLM inference.
Strictly non-agentic: handles deterministic generative calls without autonomous agent loops.
Driven by real StudentProfile and Learning Twin states.
"""

from typing import Any, Dict, Optional
from eduadapt.inference.base import BaseLLMClient, GenerationResult
from eduadapt.interfaces.rag import RAGInterface
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.personalization import PersonalizationEngine, PersonalizationContext
from eduadapt.teaching.response_schema import ResponseParser, TeachingResponse


class PersonalizedContentGenerator:
    """Generates personalized learning content adapted to real student needs."""

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
        """Generate an explanation for a PPS topic using baseline prompt."""
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
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """Generate a personalized explanation tailored to a student's real mastery profile.

        Pedagogical grounding:
        Adapts instruction according to student mastery state, performance history,
        known misconceptions, and dynamically derived instructional strategy.
        Embeds native Mermaid diagram directives and records observable generation metadata.
        """
        # 1. Derive deterministic personalization context
        p_context: PersonalizationContext = PersonalizationEngine.derive_context(
            student_profile=student_profile,
            topic=topic,
            learning_state=learning_state,
            performance_history=performance_history,
        )

        misconceptions_str = (
            "; ".join(p_context.common_misconceptions)
            if p_context.common_misconceptions
            else "None identified"
        )
        history_str = (
            performance_history
            or f"Pace: {p_context.learning_pace}, Current topic: {student_profile.current_topic}, Predicted: {p_context.predicted_mastery_level}"
        )

        # 2. Retrieve curriculum context via RAG if available
        context_str = additional_context
        retrieved_count = 0
        if self.rag is not None:
            try:
                rag_context = self.rag.retrieve(query=topic, top_k=3)
                retrieved_count = len(rag_context.documents)
                formatted_rag = rag_context.format_for_prompt()
                if context_str:
                    context_str = f"{formatted_rag}\n\nAdditional Student Context:\n{context_str}"
                else:
                    context_str = formatted_rag
            except Exception:
                context_str = context_str or "Standard PPS curriculum progression"
        elif not context_str:
            context_str = "Standard PPS curriculum progression"

        strat = p_context.strategy
        strategy_dict = strat.to_dict() if strat else {}

        # 3. Render prompt using personalized_lesson_v2 or backward-compatible templates
        prompt_rendered = False
        prompt = ""
        prompt_template_version = "personalized_lesson_v2"

        try:
            template = self.prompt_manager.get("personalized_lesson_v2")
            prompt = template.render(
                student_id=p_context.student_id,
                topic=topic,
                topic_mastery=f"{p_context.topic_mastery:.2f}",
                mastery_tier=p_context.mastery_tier,
                overall_mastery=f"{p_context.overall_mastery:.2f}",
                predicted_mastery_level=p_context.predicted_mastery_level,
                learning_pace=p_context.learning_pace,
                learning_style=p_context.preferred_learning_style,
                recommended_difficulty=p_context.recommended_difficulty,
                misconceptions=misconceptions_str,
                performance_signal=history_str,
                learning_objective=f"Understand the mechanics, memory representation, and syntax of {topic} in C.",
                curriculum_context=context_str,
                pattern_name=p_context.pattern_name,
                explanation_depth=strat.explanation_depth if strat else "balanced",
                teaching_approach=strat.teaching_approach if strat else "guided",
                cognitive_difficulty=strat.cognitive_difficulty if strat else "moderate",
                code_complexity=strat.code_complexity if strat else "standard",
                step_granularity=strat.step_granularity if strat else "moderate",
                scaffolding_level=strat.scaffolding_level if strat else "standard",
                practice_complexity=strat.practice_complexity if strat else "moderate",
                revision_strategy=strat.revision_strategy if strat else "review checks",
                diagram_directive=strat.diagram_recommendation if strat else f"Generate a clean Mermaid diagram for {topic}",
            )
            prompt_rendered = True
        except KeyError:
            pass

        if not prompt_rendered:
            try:
                template = self.prompt_manager.get("personalized_teaching")
                mastery_level_desc = f"{p_context.mastery_tier} ({p_context.topic_mastery:.2f})"
                prompt = template.render(
                    topic=topic,
                    mastery_level=mastery_level_desc,
                    performance_history=history_str,
                    misconceptions=misconceptions_str,
                    response_format=preferred_response_format,
                    context=context_str,
                )
                prompt_template_version = "personalized_teaching"
                prompt_rendered = True
            except KeyError:
                template = self.prompt_manager.get("teaching_explanation")
                prompt = template.render(
                    topic=topic,
                    learning_preference=preferred_response_format,
                    context=f"Mastery: {p_context.mastery_tier}. Misconceptions: {misconceptions_str}. {context_str}".strip(),
                )
                prompt_template_version = "teaching_explanation"

        # 4. Invoke LLM
        gen_result = self.llm_client.generate(prompt=prompt)

        # 5. Parse response and extract structured representation & diagrams
        parsed_response = ResponseParser.parse_teaching_content(
            raw_text=gen_result.content,
            topic=topic,
            diagram_type=strat.diagram_type if strat else "concept_flowchart",
            personalization_summary=p_context.personalization_summary,
            mastery_tier=p_context.mastery_tier,
        )

        # 6. Record observable personalization and diagram metadata
        metadata = dict(gen_result.metadata or {})
        metadata.update({
            "student_id": p_context.student_id,
            "topic": topic,
            "actual_mastery_used": p_context.topic_mastery,
            "overall_mastery": p_context.overall_mastery,
            "mastery_tier": p_context.mastery_tier,
            "learning_pace": p_context.learning_pace,
            "pattern_name": p_context.pattern_name,
            "selected_strategy": strategy_dict,
            "explanation_depth": strat.explanation_depth if strat else "moderate",
            "scaffolding_level": strat.scaffolding_level if strat else "moderate",
            "code_complexity": strat.code_complexity if strat else "standard",
            "diagram_decision": strat.diagram_type if strat else "concept_flowchart",
            "retrieved_context_count": retrieved_count,
            "prompt_template_version": prompt_template_version,
            "model_identifier": gen_result.model_name,
            "personalization_applied": p_context.personalization_summary,
            "personalization_applied_bullets": p_context.get_personalization_applied_bullets(),
            "diagram": parsed_response.diagram,
            "structured_response": parsed_response.to_dict(),
        })

        # Return updated GenerationResult
        return GenerationResult(
            content=gen_result.content,
            model_name=gen_result.model_name,
            prompt_tokens=gen_result.prompt_tokens,
            completion_tokens=gen_result.completion_tokens,
            metadata=metadata,
        )

    def generate_structured_lesson(
        self,
        topic: str,
        student_profile: StudentProfile,
        learning_state: Optional[Dict[str, Any]] = None,
        performance_history: Optional[str] = None,
        additional_context: str = "",
    ) -> TeachingResponse:
        """High-level helper returning validated TeachingResponse object directly."""
        gen_res = self.generate_for_student(
            topic=topic,
            student_profile=student_profile,
            learning_state=learning_state,
            performance_history=performance_history,
            additional_context=additional_context,
        )
        p_context = PersonalizationEngine.derive_context(
            student_profile=student_profile,
            topic=topic,
            learning_state=learning_state,
            performance_history=performance_history,
        )
        return ResponseParser.parse_teaching_content(
            raw_text=gen_res.content,
            topic=topic,
            diagram_type=p_context.strategy.diagram_type if p_context.strategy else "concept_flowchart",
            personalization_summary=p_context.personalization_summary,
            mastery_tier=p_context.mastery_tier,
        )

    def generate_tutor_response(
        self,
        topic: str,
        student_message: str,
        student_profile: StudentProfile,
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """MODE 2: Generate curriculum-grounded AI Tutor reply adapted to student mastery."""
        p_context = PersonalizationEngine.derive_context(
            student_profile=student_profile,
            topic=topic,
            learning_state=learning_state,
        )
        curriculum_context = "PPS Curriculum Context for " + topic
        if self.rag:
            try:
                rag_ctx = self.rag.retrieve(query=f"{topic} {student_message}", top_k=3)
                curriculum_context = rag_ctx.format_for_prompt()
            except Exception:
                pass

        template = self.prompt_manager.get("ai_tutor_dialogue")
        prompt = template.render(
            student_id=p_context.student_id,
            topic=topic,
            mastery_tier=p_context.mastery_tier,
            topic_mastery=f"{p_context.topic_mastery:.2f}",
            learning_pace=p_context.learning_pace,
            curriculum_context=curriculum_context,
            student_message=student_message,
        )
        return self.llm_client.generate(prompt=prompt)

    def generate_practice_problems(
        self,
        topic: str,
        student_profile: StudentProfile,
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """MODE 3: Generate adaptive practice problems with hint ladders."""
        p_context = PersonalizationEngine.derive_context(
            student_profile=student_profile,
            topic=topic,
            learning_state=learning_state,
        )
        curriculum_context = "PPS Curriculum Context for " + topic
        if self.rag:
            try:
                rag_ctx = self.rag.retrieve(query=f"{topic} practice", top_k=2)
                curriculum_context = rag_ctx.format_for_prompt()
            except Exception:
                pass

        misconceptions_str = "; ".join(p_context.common_misconceptions) if p_context.common_misconceptions else "None"
        template = self.prompt_manager.get("practice_generation")
        strat = p_context.strategy
        prompt = template.render(
            topic=topic,
            mastery_tier=p_context.mastery_tier,
            topic_mastery=f"{p_context.topic_mastery:.2f}",
            recommended_difficulty=p_context.recommended_difficulty,
            misconceptions=misconceptions_str,
            curriculum_context=curriculum_context,
            cognitive_difficulty=strat.cognitive_difficulty if strat else "moderate",
            scaffolding_level=strat.scaffolding_level if strat else "guided",
            code_complexity=strat.code_complexity if strat else "standard",
        )
        return self.llm_client.generate(prompt=prompt)

    def generate_formative_feedback(
        self,
        topic: str,
        problem_description: str,
        student_code: str,
        student_profile: Optional[StudentProfile] = None,
    ) -> GenerationResult:
        """MODE 4: Generate formative code feedback with progressive hints."""
        mastery_tier = "Intermediate"
        if student_profile:
            p_context = PersonalizationEngine.derive_context(student_profile=student_profile, topic=topic)
            mastery_tier = p_context.mastery_tier

        template = self.prompt_manager.get("formative_feedback_v2")
        prompt = template.render(
            topic=topic,
            mastery_tier=mastery_tier,
            problem_description=problem_description,
            student_code=student_code,
        )
        return self.llm_client.generate(prompt=prompt)

    def generate_adaptive_roadmap(
        self,
        target_competency: str,
        topic: str,
        student_profile: StudentProfile,
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """MODE 5: Generate adaptive milestone roadmap grounded in PPS curriculum."""
        p_context = PersonalizationEngine.derive_context(
            student_profile=student_profile,
            topic=topic,
            learning_state=learning_state,
        )
        curriculum_context = "PPS Curriculum progression"
        if self.rag:
            try:
                rag_ctx = self.rag.retrieve(query=topic, top_k=2)
                curriculum_context = rag_ctx.format_for_prompt()
            except Exception:
                pass

        template = self.prompt_manager.get("adaptive_roadmap_v2")
        prompt = template.render(
            target_competency=target_competency,
            topic=topic,
            topic_mastery=f"{p_context.topic_mastery:.2f}",
            mastery_tier=p_context.mastery_tier,
            learning_pace=p_context.learning_pace,
            recommended_difficulty=p_context.recommended_difficulty,
            curriculum_context=curriculum_context,
        )
        return self.llm_client.generate(prompt=prompt)
