"""Tests para OCR."""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.schemas.ocr import OCRData, OCRSuccessResponse
from app.services.ocr_service import OCRService


class TestOCRService:
    """Tests para el servicio OCR."""

    def test_calculate_confidence_with_results(self):
        """Test cálculo de confianza con resultados."""
        service = OCRService()

        # Simular resultado de OCR
        mock_result = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Hola", 0.95)],
                [[[0, 30], [100, 30], [100, 50], [0, 50]], ("Mundo", 0.87)],
            ]
        ]

        confidence = service._calculate_confidence(mock_result)
        assert confidence == pytest.approx(0.91, rel=0.01)

    def test_calculate_confidence_empty(self):
        """Test cálculo de confianza vacío."""
        service = OCRService()

        assert service._calculate_confidence([]) == 0.0
        assert service._calculate_confidence(None) == 0.0

    def test_detect_language(self):
        """Test detección de idioma."""
        service = OCRService()

        # Por ahora solo verifica que devuelve el lang configurado
        lang = service._detect_language("Hola mundo")
        assert lang == "es"

    def test_extract_pdf_text(self):
        """Test extracción de texto de PDF."""
        # Crear un PDF simple con texto
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.set_text("Este es un texto de prueba")

        pdf_bytes = doc.tobytes()
        doc.close()

        service = OCRService()
        text, pages = service.extract_pdf_text(pdf_bytes)

        assert "texto de prueba" in text
        assert pages == 1

    def test_pdf_has_text_true(self):
        """Test detección de PDF con texto."""
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.set_text("Este es un texto de prueba con suficientes caracteres")

        pdf_bytes = doc.tobytes()
        doc.close()

        service = OCRService()
        assert service.pdf_has_text(pdf_bytes) is True

    def test_pdf_has_text_false(self):
        """Test detección de PDF sin texto (escaneado)."""
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        # PDF sin texto

        pdf_bytes = doc.tobytes()
        doc.close()

        service = OCRService()
        assert service.pdf_has_text(pdf_bytes) is False


class TestOCRRoutes:
    """Tests para las rutas OCR."""

    @pytest.fixture
    def mock_ocr_service(self):
        """Mock del servicio OCR."""
        with patch("app.api.routes.ocr.ocr_service") as mock:
            mock.process_file.return_value = (
                "Texto extraído",
                0.95,
                "es",
                1,
                "ocr",
            )
            yield mock

    def test_get_file_type_image(self):
        """Test detección de tipo imagen."""
        from app.api.routes.ocr import get_file_type
        from fastapi import UploadFile

        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/png"
        mock_file.filename = "test.png"

        assert get_file_type(mock_file) == "image"

    def test_get_file_type_pdf(self):
        """Test detección de tipo PDF."""
        from app.api.routes.ocr import get_file_type
        from fastapi import UploadFile

        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "application/pdf"
        mock_file.filename = "test.pdf"

        assert get_file_type(mock_file) == "pdf"

    def test_get_file_type_by_extension(self):
        """Test detección por extensión."""
        from app.api.routes.ocr import get_file_type
        from fastapi import UploadFile

        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = ""  # Sin content-type
        mock_file.filename = "test.jpg"

        assert get_file_type(mock_file) == "image"

    def test_get_file_type_invalid(self):
        """Test archivo inválido."""
        from app.api.routes.ocr import get_file_type
        from fastapi import UploadFile

        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "application/json"
        mock_file.filename = "test.json"

        assert get_file_type(mock_file) is None


class TestOCRSchemas:
    """Tests para los schemas."""

    def test_ocr_data_model(self):
        """Test modelo OCRData."""
        data = OCRData(
            text="Hola mundo",
            confidence=0.95,
            source_type="ocr",
            pages=1,
            language_detected="es",
        )

        assert data.text == "Hola mundo"
        assert data.confidence == 0.95
        assert data.source_type == "ocr"

    def test_ocr_success_response(self):
        """Test respuesta exitosa."""
        response = OCRSuccessResponse(
            success=True,
            data=OCRData(
                text="Texto",
                confidence=0.9,
                source_type="pdf_text",
                pages=1,
                language_detected="es",
            ),
        )

        assert response.success is True
        assert response.data.source_type == "pdf_text"
