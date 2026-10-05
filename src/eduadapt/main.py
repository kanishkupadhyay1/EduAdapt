"""EduAdapt Generative AI Module entry point.

Initializes the system, wires up generation services, and demonstrates basic operations.
Strictly non-agentic: handles direct deterministic generative calls.
"""

import sys
import logging
from typing import Optional
from eduadapt.config import Settings, get_settings
from eduadapt.inference.base import BaseLLMClient, MockLLMClient
from eduadapt.inference.ollama import OllamaLLMClient
from eduadapt.prompts.templates import PromptManager
from eduadapt.teaching.generator import PersonalizedContentGenerator
from eduadapt.feedback.evaluator import FeedbackGenerator
from eduadapt.roadmap.planner import RoadmapGenerator


def configure_logging(level: str = "INFO") -> None:
    """Configure basic logging format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """Instantiate the configured LLM client.

    Raises:
        ValueError: If an unsupported LLM provider is configured.
    """
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockLLMClient(model_name=settings.llm_model_name)
    elif provider == "ollama":
        return OllamaLLMClient(
            base_url=settings.llm_api_base or "http://localhost:11434",
            model_name=settings.llm_model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider '{settings.llm_provider}'. "
            "Supported providers are: 'mock', 'ollama'."
        )


def build_app(settings: Optional[Settings] = None):
    """Factory creating and wiring the Generative AI core services."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger("eduadapt.main")

    logger.info("Initializing EduAdapt Generative AI Module [%s]", settings.app_env)
    logger.info("Configured LLM Provider: %s (Model: %s)", settings.llm_provider, settings.llm_model_name)

    # Initialize components
    llm_client = create_llm_client(settings)
    prompt_manager = PromptManager()

    teaching_service = PersonalizedContentGenerator(
        llm_client=llm_client, prompt_manager=prompt_manager
    )
    feedback_service = FeedbackGenerator(
        llm_client=llm_client, prompt_manager=prompt_manager
    )
    roadmap_service = RoadmapGenerator(
        llm_client=llm_client, prompt_manager=prompt_manager
    )

    return {
        "settings": settings,
        "llm_client": llm_client,
        "prompt_manager": prompt_manager,
        "teaching_service": teaching_service,
        "feedback_service": feedback_service,
        "roadmap_service": roadmap_service,
    }


def main():
    """Main execution function."""
    app = build_app()
    logger = logging.getLogger("eduadapt.main")
    logger.info("EduAdapt Generative AI Module successfully initialized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
