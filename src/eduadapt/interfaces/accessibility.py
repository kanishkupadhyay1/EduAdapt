"""Interface contract for external Accessibility module.

Owned by the Accessibility team member. Defines how generated content is handed off or transformed.
"""

from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel


class AccessibilityFormat(BaseModel):
    """Specification of accessibility preferences requested for a student."""

    modality: Literal["text", "simplified_text", "screen_reader_optimized"] = (
        "text"
    )
    high_contrast_support: bool = False
    include_audio_descriptions: bool = False


class AccessibilityInterface(ABC):
    """Abstract interface defining the contract with the Accessibility module."""

    @abstractmethod
    def transform_content(
        self,
        raw_text: str,
        accessibility_format: AccessibilityFormat,
    ) -> str:
        """Transform generated pedagogical content according to accessibility standards."""
        pass
