"""Routes de OCR."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.ocr import (
    OCRErrorDetail,
    OCRErrorResponse,
    OCRData,
    OCRSuccessResponse,
)
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# Limitar a 3 OCR en paralelo
_ocr_semaphore = asyncio.Semaphore(3)

# Tipos de archivos permitidos
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
ALLOWED_PDF_TYPES = {"application/pdf"}


def get_file_type(file: UploadFile) -> str | None:
    """Determina el tipo de archivo."""
    content_type = file.content_type or ""

    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if content_type in ALLOWED_PDF_TYPES:
        return "pdf"

    #También verificar por extensión
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return "image"
    if ext == ".pdf":
        return "pdf"

    return None


@router.post(
    "",
    response_model=OCRSuccessResponse,
    responses={
        400: {"model": OCRErrorResponse, "description": "Archivo inválido"},
        413: {"model": OCRErrorResponse, "description": "Archivo muy grande"},
        500: {"model": OCRErrorResponse, "description": "Error interno"},
    },
)
async def process_ocr(file: UploadFile = File(...)):
    """Procesa un archivo (imagen o PDF) y extrae texto usando OCR.

    - **file**: Archivo de imagen (JPG, PNG) o PDF de 1 página
    - **returns**: Texto extraído con metadata de confianza e idioma
    """
    logger.info(f"Recibido archivo: {file.filename}, tipo: {file.content_type}")

    # Validar tipo de archivo
    file_type = get_file_type(file)
    if file_type is None:
        logger.warning(f"Tipo de archivo no soportado: {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "Solo se aceptan imágenes (JPG, PNG) o PDFs",
            },
        )

    # Leer contenido
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Error leyendo archivo: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "READ_ERROR",
                "message": "Error al leer el archivo",
            },
        )

    # Validar tamaño
    if len(contents) > settings.max_file_size:
        logger.warning(f"Archivo demasiado grande: {len(contents)} bytes")
        raise HTTPException(
            status_code=413,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"El archivo excede el límite de {settings.max_file_size // (1024*1024)}MB",
            },
        )

    # Procesar OCR (max 3 en paralelo)
    try:
        async with _ocr_semaphore:
            text, confidence, language, pages, source_type = await asyncio.to_thread(
                ocr_service.process_file, contents, file_type
            )

        logger.info(
            f"OCR completado: {len(text)} caracteres, confianza={confidence:.2f}, "
            f"tipo={source_type}, paginas={pages}"
        )

        return OCRSuccessResponse(
            success=True,
            data=OCRData(
                text=text,
                confidence=confidence,
                source_type=source_type,
                pages=pages,
                language_detected=language,
            ),
        )

    except Exception as e:
        logger.error(f"Error en OCR: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "OCR_ERROR",
                "message": f"Error procesando el OCR: {str(e)}",
            },
        )
