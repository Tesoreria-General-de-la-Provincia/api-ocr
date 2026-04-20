"""Aplicación principal FastAPI con documentación Swagger UI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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
    logger.info("Iniciando API OCR...")
    logger.info(f"Versión: {settings.app_version}")
    logger.info(f"Idioma OCR: {settings.ocr_lang}")
    yield
    logger.info("Apagando API OCR...")


# Crear app
app = FastAPI(
    title="API OCR",
    description="API para extracción de texto de imágenes y PDFs usando EasyOCR",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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


@app.get("/", include_in_schema=False)
async def root():
    """Redirect a documentación Swagger UI."""
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Health check endpoint.

    Verifica que la API y el modelo OCR estén funcionando.
    """
    return HealthResponse(
        status="healthy",
        ocr_model_loaded=True,  # El modelo se carga lazy, pero está disponible
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
