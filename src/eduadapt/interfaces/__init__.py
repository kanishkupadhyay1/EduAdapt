"""Future integration interfaces for external modules owned by team members.

Defines schemas and contracts for:
- RAG (external retrieval)
- Student Modeling (mastery, preferences, learning style)
- Accessibility (formatting, narration, alternative modalities)
"""

from .rag import RAGContext, RAGInterface
from .student_model import StudentProfile, StudentModelInterface
from .accessibility import AccessibilityFormat, AccessibilityInterface

__all__ = [
    "RAGContext",
    "RAGInterface",
    "StudentProfile",
    "StudentModelInterface",
    "AccessibilityFormat",
    "AccessibilityInterface",
]
