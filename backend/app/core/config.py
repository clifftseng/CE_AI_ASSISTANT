import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:8080"

    DATA_DIR: str = "/data"
    MAX_FILE_SIZE_MB: int = 50
    TOTAL_UPLOAD_LIMIT_MB: int = 200
    
    ALLOWED_EXCEL_EXTS: str = ".xlsx,.xls"
    ALLOWED_PDF_EXTS: str = ".pdf"

    # -- AOAI Configurations --
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_API_VER: str | None = None
    AZURE_OPENAI_DEPLOYMENT: str | None = None

    # -- Document Intelligence Configurations --
    DI_ENDPOINT: str | None = None
    DI_KEY: str | None = None

    # --- S3 Compatible Storage (Optional - TODO) ---
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str | None = None

    # -- MongoDB Configurations --
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "simplo_ai"

    class Config:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()