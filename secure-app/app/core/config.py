from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Moa Community - Secure"
    database_url: str = "postgresql+psycopg://web_secure:web_secure@localhost:5434/web_secure"
    session_secret: str
    backup_signing_key: str
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_secrets(self):
        if len(self.session_secret) < 32 or len(self.backup_signing_key) < 32:
            raise ValueError("SESSION_SECRET and BACKUP_SIGNING_KEY must be at least 32 characters")
        if self.session_secret == self.backup_signing_key:
            raise ValueError("Session and backup keys must be independent")
        if "replace" in self.session_secret.lower() or "replace" in self.backup_signing_key.lower():
            raise ValueError("Replace example secrets before running the secure app")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
