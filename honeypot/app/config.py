"""
Configuration management for the honeypot API.
"""

from pydantic_settings import BaseSettings
from pydantic import HttpUrl, Field
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Keys - No defaults for security
    api_key: str = ""
    gemini_api_key: str = ""

    # Server Configuration
    port: int = 7860
    host: str = "0.0.0.0"

    # Performance
    disable_delays: bool = False
    max_concurrent_requests: int = 50

    # Session Management
    session_ttl_seconds: int = 3600  # 1 hour
    cleanup_interval_seconds: int = 300  # 5 minutes
    max_session_history: int = 20

    # Rate Limiting
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    # LLM Configuration
    llm_timeout_seconds: int = 30
    max_llm_retries: int = 3

    # Logging
    log_level: str = "INFO"

    # Webhook Integration
    intel_webhook_url: Optional[HttpUrl] = (
        None  # URL to send extracted intelligence alerts
    )
    webhook_timeout_seconds: int = 5
    webhook_enabled: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


# Validate required settings
def validate_settings():
    """Validate that required settings are configured."""
    if not settings.api_key:
        raise ValueError(
            "API_KEY environment variable must be set. "
            "This is required for authentication."
        )


# Run validation
validate_settings()
