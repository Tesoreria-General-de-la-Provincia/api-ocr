"""Benchmark OCR para medir tiempos."""

import io
import time

from PIL import Image, ImageDraw, ImageFont

from app.services.ocr_service import OCRService


def create_image(text: str, size: tuple = (800, 200), font_size: int = 36) -> Image.Image:
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 50), text, fill="black", font=font)
    return img


def bench():
    service = OCRService()

    img = create_image("Factura #12345 Total: $1,500.00")

    # Warmup (carga el modelo)
    print("Cargando modelo...")
    t0 = time.perf_counter()
    service.process_image(img)
    load_time = time.perf_counter() - t0
    print(f"  Primera llamada (carga modelo): {load_time:.2f}s")

    # Benchmark: 3 llamadas con defaults actuales
    print("\nDefaults actuales (readtext sin params):")
    times = []
    for i in range(3):
        t0 = time.perf_counter()
        text, conf, lang = service.process_image(img)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s  conf={conf:.2f}  text='{text}'")
    print(f"  Promedio: {sum(times)/len(times):.2f}s")


if __name__ == "__main__":
    bench()
