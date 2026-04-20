"""Servicio de OCR con EasyOCR."""

import io
import logging
from typing import Literal

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Servicio de OCR usando EasyOCR."""

    def __init__(self):
        """Inicializa el servicio OCR."""
        self._reader = None

    @property
    def reader(self):
        """Lazy loading del modelo OCR."""
        if self._reader is None:
            logger.info("Inicializando modelo EasyOCR...")
            import easyocr

            self._reader = easyocr.Reader(
                lang_list=[settings.ocr_lang, "en"],
                gpu=False,
                verbose=False,
            )
            logger.info("Modelo EasyOCR inicializado")
        return self._reader

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

    def process_image(self, image: Image.Image) -> tuple[str, float, str]:
        """Procesa una imagen con OCR.

        Returns:
            tuple: (texto, confianza, idioma)
        """
        # Convertir PIL Image a numpy array
        img_array = np.array(image)

        # EasyOCR espera RGB
        if img_array.ndim == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]

        # OCR
        logger.info("Ejecutando OCR...")
        results = self.reader.readtext(img_array)

        # Extraer texto y confianza
        text_parts = []
        confidences = []

        for detection in results:
            bbox, text, confidence = detection
            text_parts.append(text)
            confidences.append(confidence)

        full_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return full_text, avg_confidence, settings.ocr_lang

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

    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto (básico).

        Returns:
            str: código ISO del idioma o 'unknown'
        """
        return settings.ocr_lang


# Instancia global del servicio (lazy loading)
ocr_service = OCRService()
