"""Interface contract for external Student Modeling module.

Owned by the Student Modeling team member. This module consumes student profile data.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """Student profile representation provided by the Student Modeling module."""

    student_id: str
    current_topic: str
    mastery_levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Topic-wise mastery scores between 0.0 and 1.0",
    )
    learning_style: str = "balanced"
    preferred_pace: str = "moderate"
    common_misconceptions: List[str] = Field(default_factory=list)


class StudentModelInterface(ABC):
    """Abstract interface defining the contract with the Student Modeling module."""

    @abstractmethod
    def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Fetch the current student profile and mastery state."""
        pass
