import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

project_root = Path(__file__).resolve().parents[3]
default_storage = project_root / "storage"

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocSphere - AI Document Intelligence"
    API_V1_STR: str = "/api"
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "image/png",
        "image/jpeg",
        "image/webp"
    ]
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(default_storage)))
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(default_storage / "uploads")))
    DB_PATH: Path = Path(os.getenv("DB_PATH", str(default_storage / "docintel.db")))
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    OLLAMA_BASE_URL: str | None = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "auto")
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
