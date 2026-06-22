"""Configuration management using environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_settings() -> dict:
    """Load and validate configuration from environment."""
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API_KEY not found. "
            "Copy .env.example to .env and add your API key."
        )

    return {
        "api_key": api_key,
        "model": os.getenv("LLM_MODEL", "deepseek-chat"),
        "base_url": os.getenv("API_BASE_URL", "https://api.deepseek.com/v1"),
        "max_tokens": int(os.getenv("MAX_TOKENS", "4096")),
        "temperature": float(os.getenv("TEMPERATURE", "0.3")),
    }
