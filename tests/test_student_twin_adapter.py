"""Tests for Member 3 Learning Twin adapter."""

from eduadapt.adapters.student_twin_adapter import LearningTwinAdapter
from eduadapt.interfaces.student_model import StudentProfile, StudentModelInterface


def test_adapter_implements_student_model_interface():
    adapter = LearningTwinAdapter()
    assert isinstance(adapter, StudentModelInterface)


def test_s001_mapping_to_canonical_profile():
    adapter = LearningTwinAdapter()
    profile = adapter.get_profile("S001", topic="Pointers")

    assert profile is not None
    assert isinstance(profile, StudentProfile)
    # 1. Student ID is preserved
    assert profile.student_id == "S001"
    # 2. Topic is assigned
    assert profile.current_topic == "Pointers"
    # 3. Mastery is mapped correctly for topic (Member 3 has 1.0 for S001)
    assert "Pointers" in profile.mastery_levels
    assert profile.mastery_levels["Pointers"] == 1.0
    # 4. Learning pace is mapped correctly
    assert profile.preferred_pace in ("fast", "Fast")
    # 5. Default safe values for fields not provided by Member 3
    assert profile.learning_style == "balanced"
    assert profile.common_misconceptions == []


def test_unknown_student_returns_none():
    adapter = LearningTwinAdapter()
    profile = adapter.get_profile("NON_EXISTENT_STUDENT")
    assert profile is None


def test_default_topic_fallback():
    adapter = LearningTwinAdapter(default_topic="Functions")
    profile = adapter.get_profile("S001")
    assert profile is not None
    assert profile.current_topic == "Functions"
    assert profile.mastery_levels.get("Functions") == 1.0
