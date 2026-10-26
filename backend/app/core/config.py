import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "AICTE Application Validation Platform"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aicte_validation.db")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # File Storage Configuration
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # 'local' or 's3'
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "documents")))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg"]
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()

# Ensure local storage directory exists
if settings.STORAGE_TYPE == "local":
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
