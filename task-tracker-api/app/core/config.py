"""
Application configuration module.

Loads environment variables from the .env file using python-dotenv
and exposes them as simple, typed settings for the rest of the app to use.
"""
import os
from dotenv import load_dotenv

# Load variables from a local .env file into the process environment.
# If .env is missing, this simply does nothing and os.getenv() falls
# back to the defaults below.
load_dotenv()


class Settings:
    """Holds application configuration values read from environment variables."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.port: int = int(os.getenv("PORT", "8000"))


# Single shared settings instance used across the application.
settings = Settings()