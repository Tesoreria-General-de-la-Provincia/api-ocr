"""Schemas Pydantic para OCR."""

from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """Resultado del OCR."""

    text: str = Field(description="Texto extraído del documento")
    confidence: float = Field(description="Confianza promedio del OCR (0-1)")
    source_type: str = Field(description="'ocr' o 'pdf_text' según la fuente")
    pages: int = Field(default=1, description="Cantidad de páginas procesadas")
    language_detected: str = Field(default="es", description="Idioma detectado")


class OCRData(BaseModel):
    """Datos del OCR."""

    text: str
    confidence: float
    source_type: str
    pages: int
    language_detected: str


class OCRSuccessResponse(BaseModel):
    """Respuesta exitosa del OCR."""

    success: bool = True
    data: OCRData


class OCRErrorDetail(BaseModel):
    """Detalle del error."""

    code: str
    message: str


class OCRErrorResponse(BaseModel):
    """Respuesta de error del OCR."""

    success: bool = False
    error: OCRErrorDetail


class HealthResponse(BaseModel):
    """Respuesta del health check."""

    status: str
    ocr_model_loaded: bool
    version: str


# Union type para respuestas
OCRResponse = OCRSuccessResponse | OCRErrorResponse
