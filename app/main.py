"""Aplicación principal FastAPI con documentación Scalar."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from scalar_fastapi import get_scalar_api_reference

from app.api.routes import ocr
from app.core.config import settings
from app.schemas.ocr import HealthResponse

# Configurar logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación."""
    from app.services.ocr_service import ocr_service

    logger.info("Iniciando API OCR...")
    logger.info(f"Versión: {settings.app_version}")
    logger.info(f"Idioma OCR: {settings.ocr_lang}")
    logger.info("Precargando modelo OCR...")
    _ = ocr_service.reader  # Forzar carga del modelo al startup
    logger.info("Modelo OCR listo")
    yield
    logger.info("Apagando API OCR...")


# Crear app (sin docs de Swagger/ReDoc)
app = FastAPI(
    title="API OCR",
    description="API para extracción de texto de imágenes y PDFs usando EasyOCR",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routes
app.include_router(ocr.router)


@app.get("/scalar", include_in_schema=False)
async def scalar_docs():
    """Documentación interactiva con Scalar."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="API OCR",
    )


@app.get("/", include_in_schema=False)
async def root():
    """Redirect a documentación Scalar."""
    return RedirectResponse(url="/scalar", status_code=307)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Health check endpoint.

    Verifica que la API y el modelo OCR estén funcionando.
    """
    from app.services.ocr_service import ocr_service

    return HealthResponse(
        status="healthy",
        ocr_model_loaded=ocr_service._reader is not None,
        version=settings.app_version,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
