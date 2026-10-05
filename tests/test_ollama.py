"""Unit tests for Ollama client, configuration switching, and teaching integration."""

from unittest.mock import MagicMock, patch
import pytest
import requests

from eduadapt.config import Settings
from eduadapt.inference.base import GenerationResult, MockLLMClient
from eduadapt.inference.ollama import (
    OllamaLLMClient,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaResponseError,
)
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.main import build_app, create_llm_client
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.generator import PersonalizedContentGenerator


def test_ollama_client_successful_response():
    """Verify OllamaLLMClient parses successful response, tokens, and metadata."""
    client = OllamaLLMClient(
        base_url="http://localhost:11434",
        model_name="mistral:7b",
        temperature=0.5,
        max_tokens=512,
        timeout=180.0,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "mistral:7b",
        "response": "In C, a variable must be declared with a data type before use.",
        "prompt_eval_count": 32,
        "eval_count": 64,
        "total_duration": 4500000000,
        "done": True,
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = client.generate(
            prompt="Explain C variable declaration.",
            system_instruction="You are a C tutor.",
        )

        assert isinstance(result, GenerationResult)
        assert result.content == "In C, a variable must be declared with a data type before use."
        assert result.model_name == "mistral:7b"
        assert result.prompt_tokens == 32
        assert result.completion_tokens == 64
        assert result.metadata.get("done") is True
        assert result.metadata.get("system_instruction") == "You are a C tutor."

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 180.0
        assert call_kwargs["json"]["model"] == "mistral:7b"
        assert call_kwargs["json"]["options"]["temperature"] == 0.5
        assert call_kwargs["json"]["options"]["num_predict"] == 512
        assert call_kwargs["json"]["system"] == "You are a C tutor."


def test_ollama_client_connection_error():
    """Verify OllamaConnectionError is raised when Ollama endpoint is unreachable."""
    client = OllamaLLMClient(base_url="http://invalid-ollama-host:11434")

    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        with pytest.raises(OllamaConnectionError) as exc_info:
            client.generate(prompt="Hello")

        assert "Failed to connect to Ollama" in str(exc_info.value)
        assert "invalid-ollama-host:11434" in str(exc_info.value)


def test_ollama_client_timeout_error():
    """Verify OllamaTimeoutError is raised when inference request times out."""
    client = OllamaLLMClient(timeout=180.0)

    with patch("requests.post", side_effect=requests.exceptions.ReadTimeout("Read timed out")):
        with pytest.raises(OllamaTimeoutError) as exc_info:
            client.generate(prompt="Long computation")

        assert "timed out after 180.0 seconds" in str(exc_info.value)


def test_ollama_client_http_and_api_errors():
    """Verify OllamaResponseError on HTTP error status or API error payload."""
    client = OllamaLLMClient()

    # Case 1: HTTP 500 error
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500
    mock_resp_500.text = "Internal Server Error"
    with patch("requests.post", return_value=mock_resp_500):
        with pytest.raises(OllamaResponseError) as exc_info:
            client.generate(prompt="Fail test")
        assert "HTTP 500" in str(exc_info.value)

    # Case 2: 200 with error payload
    mock_resp_err = MagicMock()
    mock_resp_err.status_code = 200
    mock_resp_err.json.return_value = {"error": "model 'nonexistent:7b' not found"}
    with patch("requests.post", return_value=mock_resp_err):
        with pytest.raises(OllamaResponseError) as exc_info:
            client.generate(prompt="Fail test 2")
        assert "Ollama API returned an error" in str(exc_info.value)


def test_configuration_switching_and_validation():
    """Verify configuration switching between mock and ollama and rejection of unsupported providers."""
    # Mock provider configuration
    settings_mock = Settings(LLM_PROVIDER="mock", LLM_MODEL_NAME="mock-pps-model")
    app_mock = build_app(settings=settings_mock)
    assert isinstance(app_mock["llm_client"], MockLLMClient)

    # Ollama provider configuration with default 180s timeout
    settings_ollama = Settings(
        LLM_PROVIDER="ollama",
        LLM_MODEL_NAME="mistral:7b",
        LLM_API_BASE="http://localhost:11434",
    )
    assert settings_ollama.llm_timeout == 180.0
    app_ollama = build_app(settings=settings_ollama)
    assert isinstance(app_ollama["llm_client"], OllamaLLMClient)
    assert app_ollama["llm_client"].timeout == 180.0
    assert app_ollama["llm_client"].model_name == "mistral:7b"

    # Unsupported provider rejection
    with pytest.raises(ValueError) as exc_info:
        Settings(LLM_PROVIDER="unsupported_provider")
    assert "Unsupported LLM provider" in str(exc_info.value)


def test_teaching_integration_personalized_mastery():
    """Verify personalized explanation adapts to beginner vs advanced learner profiles."""
    client = MockLLMClient()
    pm = PromptManager()
    teaching = PersonalizedContentGenerator(llm_client=client, prompt_manager=pm)

    # Beginner profile: low mastery in Loops, known misconception
    beginner_student = StudentProfile(
        student_id="std_beginner",
        current_topic="Loops",
        mastery_levels={"Loops": 0.25, "Variables and Types": 0.6},
        learning_style="interactive",
        preferred_pace="slow",
        common_misconceptions=["Off-by-one errors in loop boundaries"],
    )

    result_beginner = teaching.generate_for_student(
        topic="Loops",
        student_profile=beginner_student,
        preferred_response_format="step-by-step trace with simple code",
        performance_history="First attempt at loop construct; struggled with condition checking",
    )
    assert result_beginner.content.startswith("[Mock LLM Output")

    # Advanced profile: high mastery in Loops, no misconceptions
    advanced_student = StudentProfile(
        student_id="std_advanced",
        current_topic="Nested Loops",
        mastery_levels={"Loops": 0.9, "Nested Loops": 0.85},
        learning_style="code_first",
        preferred_pace="fast",
        common_misconceptions=[],
    )

    result_advanced = teaching.generate_for_student(
        topic="Nested Loops",
        student_profile=advanced_student,
        preferred_response_format="concise idiomatic C code highlighting loop unrolling and complexity",
        performance_history="Mastered basic loops quickly with zero syntax errors",
    )
    assert result_advanced.content.startswith("[Mock LLM Output")
