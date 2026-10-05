"""Inference package for EduAdapt Generative AI module."""

from .base import BaseLLMClient, GenerationResult, MockLLMClient
from .ollama import (
    OllamaLLMClient,
    OllamaError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaResponseError,
)

__all__ = [
    "BaseLLMClient",
    "GenerationResult",
    "MockLLMClient",
    "OllamaLLMClient",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaTimeoutError",
    "OllamaResponseError",
]
