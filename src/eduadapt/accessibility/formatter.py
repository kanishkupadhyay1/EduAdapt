"""Accessibility Content Formatter (Member 4 Contribution).

Transforms structured teaching, assessment, and feedback session results into
clean, accessible representations with structured sections:
- Topic
- Learning Level
- Explanation
- Code Examples
- Practice Question
- Feedback Guidance
- PPS Curriculum Sources
"""

from typing import Any, Dict, List, Optional
from eduadapt.evaluation.c_executor import extract_c_code


class AccessibilityFormatter:
    """Transforms learning session results into an accessible structured representation."""

    @staticmethod
    def format_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format a session result dictionary into accessible views.

        Args:
            session_data: The full structured dictionary from run_learning_session.

        Returns:
            Dictionary with formatted accessible components and plain readable transcript.
        """
        student = session_data.get("student", {})
        profile = session_data.get("profile", {})
        curriculum = session_data.get("curriculum", {})
        teaching = session_data.get("teaching", {})
        assessment = session_data.get("assessment", {})
        feedback = session_data.get("feedback", {})

        topic = profile.get("current_topic") or curriculum.get("topic") or "Programming Concept"
        learning_level = (
            student.get("predicted_mastery_level")
            or student.get("recommended_difficulty")
            or "Standard"
        )
        content_text = teaching.get("generated_teaching_content", "")
        extracted_code = extract_c_code(content_text)

        # Sources summary
        sources_list: List[Dict[str, Any]] = []
        for chunk in curriculum.get("retrieved_chunks", []):
            sources_list.append({
                "source": chunk.get("source"),
                "slide_or_page": chunk.get("slide_or_page"),
                "module": chunk.get("unit_or_module"),
            })

        # Screen-reader friendly text summary
        screen_reader_summary = (
            f"Lesson on {topic} for {learning_level} level student {student.get('student_id', '')}. "
            f"Grounding verified with {len(sources_list)} curriculum slides. "
            f"Includes interactive practice assessment question with feedback."
        )

        return {
            "topic": topic,
            "learning_level": learning_level,
            "preferred_pace": profile.get("preferred_pace", "moderate"),
            "explanation": content_text,
            "examples": extracted_code or "No standalone C code block present",
            "practice_question": {
                "question": assessment.get("question", ""),
                "options": assessment.get("options", []),
                "explanation": assessment.get("explanation", ""),
            },
            "feedback": feedback.get("feedback", "No feedback provided."),
            "sources": sources_list,
            "screen_reader_summary": screen_reader_summary,
            "modality": "screen_reader_and_text_optimized",
        }
