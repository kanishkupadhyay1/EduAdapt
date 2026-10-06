"""Adapter integrating Member 3's Learning Twin with EduAdapt's StudentProfile contract."""

from typing import Optional

from eduadapt.interfaces.student_model import StudentModelInterface, StudentProfile
from member3.student_state import get_student_state


class LearningTwinAdapter(StudentModelInterface):
    """Translates Member 3 Learning Twin outputs into canonical EduAdapt StudentProfile instances."""

    def __init__(self, default_topic: str = "General Programming") -> None:
        self.default_topic = default_topic

    def get_profile(
        self,
        student_id: str,
        topic: Optional[str] = None,
    ) -> Optional[StudentProfile]:
        """Fetch Member 3 student state and map to canonical StudentProfile.

        Args:
            student_id: Unique identifier for the student.
            topic: Target curriculum topic to associate with the mastery state.
                Defaults to self.default_topic if omitted.

        Returns:
            A populated StudentProfile, or None if the student does not exist.
        """
        raw_state = get_student_state(student_id)
        if raw_state is None:
            return None

        target_topic = topic or self.default_topic
        mastery_val = float(raw_state.get("mastery", 0.0))
        pace_val = str(raw_state.get("learning_pace", "moderate")).lower()

        return StudentProfile(
            student_id=str(raw_state["student_id"]),
            current_topic=target_topic,
            mastery_levels={target_topic: mastery_val},
            learning_style="balanced",
            preferred_pace=pace_val,
            common_misconceptions=[],
        )

    def get_student_profile(
        self,
        student_id: str,
        topic: Optional[str] = None,
    ) -> Optional[StudentProfile]:
        """Convenience alias for get_profile matching explicit topic parameter requests."""
        return self.get_profile(student_id=student_id, topic=topic)
