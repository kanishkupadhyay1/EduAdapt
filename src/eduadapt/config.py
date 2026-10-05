"""Configuration management for EduAdapt Generative AI module."""

from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General App Config
    app_name: str = Field(default="EduAdapt Generative AI Module", alias="APP_NAME")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # LLM Inference Configuration
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model_name: str = Field(default="mock-pps-model", alias="LLM_MODEL_NAME")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_api_base: str = Field(default="http://localhost:11434", alias="LLM_API_BASE")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")
    llm_timeout: float = Field(default=180.0, alias="LLM_TIMEOUT")

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        provider = str(v).strip().lower()
        if provider not in {"mock", "ollama"}:
            raise ValueError(
                f"Unsupported LLM provider '{v}'. Only 'mock' and 'ollama' are supported."
            )
        return provider

    # Downstream / External Integration Endpoints
    rag_service_url: str = Field(
        default="http://localhost:8001", alias="RAG_SERVICE_URL"
    )
    student_model_service_url: str = Field(
        default="http://localhost:8002", alias="STUDENT_MODEL_SERVICE_URL"
    )
    accessibility_service_url: str = Field(
        default="http://localhost:8003", alias="ACCESSIBILITY_SERVICE_URL"
    )

    # Base Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent


def get_settings() -> Settings:
    """Retrieve application settings instance."""
    return Settings()
