"""Base interfaces and lightweight mock client for LLM inference.

Follows a pure generative design without autonomous agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GenerationResult(BaseModel):
    """Encapsulates the standard output from an LLM inference call."""

    content: str
    model_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class BaseLLMClient(ABC):
    """Abstract base class for all LLM inference clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Synchronously generate a completion from the LLM."""
        pass


class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for testing and development without downloading models."""

    def __init__(self, model_name: str = "mock-pps-model"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        mock_response = f"[Mock LLM Output for prompt length {len(prompt)} chars]"
        return GenerationResult(
            content=mock_response,
            model_name=self.model_name,
            metadata={"mock": True, "system_instruction": system_instruction},
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(mock_response.split()),
        )
