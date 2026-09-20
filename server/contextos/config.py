import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONTEXTOS_")

    # Root workspace directory that agents are jailed inside
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

    # Database file location
    DATA_DIR: Path = Path(__file__).resolve().parents[2] / ".contextos"
    DB_NAME: str = "contextos.db"

    # Daemon network ports
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Process execution & sandboxing limits
    COMMAND_TIMEOUT_SECONDS: int = 30
    MAX_OUTPUT_BYTES: int = 100 * 1024  # 100 KB max buffer per command

    # Secret redaction pattern substrings/keys
    SENSITIVE_KEY_PATTERNS: list[str] = [
        "KEY", "SECRET", "TOKEN", "PASSWORD", "AUTH", "CREDENTIAL", "PRIVATE"
    ]

    @property
    def db_path(self) -> Path:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return self.DATA_DIR / self.DB_NAME

settings = Settings()
