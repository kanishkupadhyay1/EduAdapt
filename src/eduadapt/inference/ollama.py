"""Ollama LLM inference client for EduAdapt Generative AI module.

Follows a pure generative, non-agentic design implementing BaseLLMClient.
Communicates with the local Ollama instance (default: mistral:7b).
"""

from typing import Any, Dict, Optional
import requests

from eduadapt.inference.base import BaseLLMClient, GenerationResult


class OllamaError(Exception):
    """Base exception for all Ollama client errors."""

    pass


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama service is unreachable or connection is refused."""

    pass


class OllamaTimeoutError(OllamaError):
    """Raised when an inference request to Ollama times out."""

    pass


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an error response or non-200 HTTP status."""

    pass


class OllamaLLMClient(BaseLLMClient):
    """Synchronous LLM inference client connecting to a local or remote Ollama server."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "mistral:7b",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Synchronously generate a completion from Ollama.

        Args:
            prompt: User/instruction prompt.
            system_instruction: Optional system instruction.
            temperature: Sampling temperature override.
            max_tokens: Maximum completion tokens (maps to num_predict).
            timeout: HTTP request timeout override in seconds.
            **kwargs: Additional parameters passed to Ollama options.

        Returns:
            GenerationResult containing generated text, token counts, and metadata.

        Raises:
            OllamaConnectionError: If the Ollama server is unreachable.
            OllamaTimeoutError: If the request times out.
            OllamaResponseError: If the Ollama API returns an error or unexpected status.
        """
        endpoint = f"{self.base_url}/api/generate"

        eff_temp = temperature if temperature is not None else self.temperature
        eff_max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        eff_timeout = timeout if timeout is not None else self.timeout

        options: Dict[str, Any] = {}
        if eff_temp is not None:
            options["temperature"] = eff_temp
        if eff_max_tokens is not None:
            options["num_predict"] = eff_max_tokens

        options.update(kwargs)

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=eff_timeout,
            )
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as e:
            raise OllamaTimeoutError(
                f"Inference request to Ollama ({self.base_url}) timed out after {eff_timeout} seconds: {e}"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at '{self.base_url}'. "
                f"Verify that the Ollama service is running and accessible: {e}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise OllamaResponseError(f"HTTP request to Ollama failed: {e}") from e

        if response.status_code != 200:
            raise OllamaResponseError(
                f"Ollama server returned HTTP {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except ValueError as e:
            raise OllamaResponseError(f"Invalid JSON returned by Ollama server: {response.text}") from e

        if "error" in data:
            raise OllamaResponseError(f"Ollama API returned an error: {data['error']}")

        content = data.get("response", "")
        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")

        metadata: Dict[str, Any] = {
            k: v for k, v in data.items() if k not in ("response", "prompt_eval_count", "eval_count")
        }
        if system_instruction:
            metadata["system_instruction"] = system_instruction

        return GenerationResult(
            content=content,
            model_name=data.get("model", self.model_name),
            metadata=metadata,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
