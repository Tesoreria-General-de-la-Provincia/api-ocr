"""Servicio de OCR con PaddleOCR."""

import io
import logging
from typing import Literal

import fitz  # PyMuPDF
from PIL import Image
from paddleocr import PaddleOCR

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Servicio de OCR usando PaddleOCR."""

    def __init__(self):
        """Inicializa el servicio OCR."""
        self._ocr: PaddleOCR | None = None

    @property
    def ocr(self) -> PaddleOCR:
        """Lazy loading del modelo OCR."""
        if self._ocr is None:
            logger.info("Inicializando modelo PaddleOCR...")
            self._ocr = PaddleOCR(
                lang=settings.ocr_lang,
                use_angle_cls=settings.ocr_use_angle_cls,
                use_textline_orientation=settings.ocr_use_textline_orientation,
                use_doc_orientation_classify=settings.ocr_use_doc_orientation_classify,
                use_doc_unwarping=settings.ocr_use_doc_unwarping,
                show_log=False,
            )
            logger.info("Modelo PaddleOCR inicializado")
        return self._ocr

    def extract_pdf_text(self, pdf_bytes: bytes) -> tuple[str, int]:
        """Extrae texto digital de un PDF.

        Returns:
            tuple: (texto, cantidad_paginas)
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = len(doc)

        if pages > 1:
            logger.warning(f"PDF tiene {pages} páginas, solo se procesa la primera")

        text_parts = []
        for page_num in range(min(pages, 1)):  # Solo primera página
            page = doc[page_num]
            text_parts.append(page.get_text())

        doc.close()
        return "\n".join(text_parts), min(pages, 1)

    def pdf_has_text(self, pdf_bytes: bytes) -> bool:
        """Verifica si el PDF tiene texto digital suficiente."""
        text, _ = self.extract_pdf_text(pdf_bytes)
        return len(text.strip()) >= settings.pdf_min_text_length

    def convert_pdf_to_image(self, pdf_bytes: bytes) -> Image.Image:
        """Convierte la primera página de un PDF a imagen.

        Returns:
            PIL.Image: Imagen de la primera página del PDF
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]

        # Renderizar a 200 DPI para buena calidad
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_bytes = pix.tobytes("png")
        doc.close()

        return Image.open(io.BytesIO(img_bytes))

    def _calculate_confidence(self, ocr_result) -> float:
        """Calcula la confianza promedio del OCR."""
        if not ocr_result or not ocr_result[0]:
            return 0.0

        confidences = []
        for line in ocr_result[0]:
            if len(line) >= 2 and isinstance(line[1], (int, float)):
                confidences.append(float(line[1]))

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)

    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto (básico).

        Returns:
            str: código ISO del idioma o 'unknown'
        """
        # PaddleOCR ya procesó con el lang configurado, asumimos ese
        # En producción se podría usar langdetect para verificar
        return settings.ocr_lang

    def process_image(self, image: Image.Image) -> tuple[str, float, str]:
        """Procesa una imagen con OCR.

        Returns:
            tuple: (texto, confianza, idioma)
        """
        # Convertir PIL Image a bytes para PaddleOCR
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # OCR
        result = self.ocr.ocr(img_bytes.read(), cls=True)

        # Extraer texto
        text_parts = []
        for line in result[0]:
            if len(line) >= 2:
                text_parts.append(line[1][0])

        text = "\n".join(text_parts)
        confidence = self._calculate_confidence(result)
        language = self._detect_language(text)

        return text, confidence, language

    def process_file(
        self, file_bytes: bytes, file_type: Literal["image", "pdf"]
    ) -> tuple[str, float, str, int, str]:
        """Procesa un archivo (imagen o PDF).

        Args:
            file_bytes: Contenido del archivo
            file_type: 'image' o 'pdf'

        Returns:
            tuple: (texto, confianza, idioma, paginas, source_type)
        """
        if file_type == "pdf":
            # Primero intentar extraer texto digital
            if self.pdf_has_text(file_bytes):
                logger.info("PDF tiene texto digital, extrayendo sin OCR")
                text, pages = self.extract_pdf_text(file_bytes)
                return text, 1.0, self._detect_language(text), pages, "pdf_text"

            # Convertir a imagen y hacer OCR
            logger.info("PDF no tiene texto digital, aplicando OCR")
            image = self.convert_pdf_to_image(file_bytes)
            text, confidence, language = self.process_image(image)
            return text, confidence, language, 1, "ocr"

        else:
            # Es imagen directa
            image = Image.open(io.BytesIO(file_bytes))
            text, confidence, language = self.process_image(image)
            return text, confidence, language, 1, "ocr"


# Instancia global del servicio (lazy loading)
ocr_service = OCRService()
