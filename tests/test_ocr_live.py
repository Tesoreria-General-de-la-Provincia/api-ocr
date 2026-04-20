"""Tests de OCR con imágenes reales generadas."""

import io
import sys

from PIL import Image, ImageDraw, ImageFont


def create_test_image(text: str, size: tuple = (800, 200), font_size: int = 36) -> bytes:
    """Crea una imagen con texto para testing."""
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            font = ImageFont.load_default()

    draw.text((20, 50), text, fill="black", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_multiline_image(lines: list[str], size: tuple = (800, 400), font_size: int = 28) -> bytes:
    """Crea una imagen con múltiples líneas."""
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            font = ImageFont.load_default()

    y = 30
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += font_size + 15

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_low_contrast_image(text: str) -> bytes:
    """Crea imagen con bajo contraste (gris sobre gris claro)."""
    img = Image.new("RGB", (800, 200), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except OSError:
            font = ImageFont.load_default()

    draw.text((20, 50), text, fill=(150, 150, 150), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run_tests():
    """Ejecuta tests de OCR y reporta resultados."""
    from app.services.ocr_service import OCRService

    service = OCRService()

    tests = [
        {
            "name": "Texto simple en español",
            "image": create_test_image("Hola mundo esto es una prueba"),
            "expected": "hola mundo esto es una prueba",
        },
        {
            "name": "Texto en inglés",
            "image": create_test_image("Hello world this is a test"),
            "expected": "hello world this is a test",
        },
        {
            "name": "Números y símbolos",
            "image": create_test_image("Factura #12345 Total: $1,500.00"),
            "expected": "factura #12345 total: $1,500.00",
        },
        {
            "name": "Texto multilínea (documento)",
            "image": create_multiline_image([
                "REPÚBLICA ARGENTINA",
                "Documento Nacional de Identidad",
                "Nombre: Juan Martin Lavalle",
                "DNI: 12.345.678",
            ]),
            "expected": "república argentina",
        },
        {
            "name": "Bajo contraste",
            "image": create_low_contrast_image("Texto con bajo contraste"),
            "expected": "texto con bajo contraste",
        },
    ]

    print("=" * 70)
    print("TEST DE OCR - EasyOCR")
    print("=" * 70)

    for i, test in enumerate(tests, 1):
        print(f"\n--- Test {i}: {test['name']} ---")

        image = Image.open(io.BytesIO(test["image"]))
        text, confidence, language = service.process_image(image)

        text_lower = text.lower().strip()
        expected = test["expected"]
        match = expected in text_lower

        print(f"  Texto detectado : {text}")
        print(f"  Confianza       : {confidence:.4f} ({confidence*100:.1f}%)")
        print(f"  Idioma          : {language}")
        print(f"  Contiene esperado: {'SI' if match else 'NO'}")

        if not match:
            print(f"  ESPERADO (parcial): {expected}")

    print("\n" + "=" * 70)
    print("TESTS COMPLETADOS")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
