"""Benchmark: es+en vs solo es."""

import io
import time

import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_bank_receipt() -> np.ndarray:
    """Simula un comprobante bancario con texto denso."""
    img = Image.new("RGB", (600, 800), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except OSError:
        font = ImageFont.load_default()
        font_bold = font

    lines = [
        ("Galicia", font_bold),
        ("APP GALICIA", font_bold),
        ("Transferencia Hacia otro Banco", font),
        ("Nuevo Destinatario (24 hs)", font),
        ("Fecha y Hora", font),
        ("27/09/2020 14:47:03", font),
        ("Nro. de Operación: 2714486845", font),
        ("Cuenta Débito N° (CC $) 538441978", font),
        ("Importe Debitado $ 50.000,00", font),
        ("CBU: 0720019988000037063254", font),
        ("Banco: SANTANDER RIO", font),
        ("Nombre: DOMINGUEZ ESPINO FACUNDO", font),
        ("Importe Acreditado $ 50.000,00", font),
        ("Concepto: VAR", font),
    ]

    y = 30
    for text, f in lines:
        draw.text((30, y), text, fill="black", font=f)
        y += 45

    return np.array(img)


def bench():
    img = create_bank_receipt()

    # Test 1: es + en (config actual)
    print("=== Config actual: ['es', 'en'] ===")
    t0 = time.perf_counter()
    reader_dual = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
    load_dual = time.perf_counter() - t0
    print(f"  Carga modelo: {load_dual:.2f}s")

    times = []
    for i in range(3):
        t0 = time.perf_counter()
        result = reader_dual.readtext(img)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
    print(f"  OCR promedio: {sum(times)/len(times):.2f}s")
    print(f"  Detecciones: {len(result)}")

    # Test 2: solo es
    print("\n=== Solo ['es'] ===")
    t0 = time.perf_counter()
    reader_es = easyocr.Reader(["es"], gpu=False, verbose=False)
    load_es = time.perf_counter() - t0
    print(f"  Carga modelo: {load_es:.2f}s")

    times = []
    for i in range(3):
        t0 = time.perf_counter()
        result = reader_es.readtext(img)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
    print(f"  OCR promedio: {sum(times)/len(times):.2f}s")
    print(f"  Detecciones: {len(result)}")


if __name__ == "__main__":
    bench()
