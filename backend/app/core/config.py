"""
Application Configuration

Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://alexmclaughlin@localhost:5432/courtlistener"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Environment
    ENVIRONMENT: str = "development"
    RAILWAY_ENVIRONMENT: str = "development"  # Set by Railway
    PORT: int = 8000  # Set by Railway

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8001"]
    ALLOWED_ORIGINS: str = "http://localhost:3000"  # Comma-separated list

    # AWS S3
    S3_BUCKET_NAME: str = "com-courtlistener-storage"
    S3_PREFIX: str = "bulk-data/"

    # Data directory
    DATA_DIR: str = "./data"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.CORS_ORIGINS


settings = Settings()

