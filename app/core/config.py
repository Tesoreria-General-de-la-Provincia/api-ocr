"""Configuración de la aplicación."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings de la aplicación."""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_version: str = "0.1.0"

    # OCR (EasyOCR)
    ocr_lang: str = "es"

    # Límites
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    pdf_min_text_length: int = 50  # mínimo de caracteres para considerar texto digital

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
