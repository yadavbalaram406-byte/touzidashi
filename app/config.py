from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    llm_provider: str = "anthropic"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_base_url: str = "https://api.anthropic.com"

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    upload_dir: str = "data/uploads"
    database_url: str = "sqlite+aiosqlite:///data/touzidashi.db"
    max_upload_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    # Read .env directly, bypassing OS environment variables for model config
    from dotenv import dotenv_values
    import os
    env_vals = dotenv_values(".env")
    # Override specific keys from .env so they take precedence over OS env vars
    for key in ("ANTHROPIC_MODEL", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL",
                "DEEPSEEK_MODEL", "DEEPSEEK_API_KEY", "LLM_PROVIDER"):
        if key in env_vals:
            os.environ[key] = env_vals[key]
    return Settings()
