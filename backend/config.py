from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration for the Pharmesol sales agent."""

    # OpenAI
    openai_api_key: str = Field(alias="OPEN_API_KEY")
    model: str = "gpt-5.4"
    fast_model: str = "gpt-5.4-mini"

    # Resilience
    openai_max_retries: int = 3
    openai_timeout_seconds: int = 30
    max_tool_iterations: int = 10

    # Context management
    context_summary_threshold: int = 20
    context_preserve_recent: int = 6

    # Pharmacy lookup
    pharmacy_api_url: str = "https://67e14fb758cc6bf785254550.mockapi.io/pharmacies"
    pharmacy_api_timeout: int = 10

    # Guardrails
    max_email_sends_per_session: int = 3
    max_callbacks_per_session: int = 2

    model_config = {
        "env_file": [".env", "backend/.env"],
        "extra": "ignore",
    }


settings = Settings()
