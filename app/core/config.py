"""Configuración de la aplicación."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings de la aplicación."""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_version: str = "0.1.0"

    # OCR
    ocr_lang: str = "es"
    ocr_lang_list: list[str] = ["es", "en"]
    ocr_use_angle_cls: bool = False
    ocr_use_textline_orientation: bool = False
    ocr_use_doc_orientation_classify: bool = False
    ocr_use_doc_unwarping: bool = False

    # Límites
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    ocr_timeout: int = 60  # segundos
    pdf_min_text_length: int = 50  # mínimo de caracteres para considerar texto digital

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
