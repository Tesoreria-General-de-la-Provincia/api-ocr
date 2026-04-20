"""Benchmark: impacto del canvas_size y resize en OCR."""

import io
import time

import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_large_receipt(width: int = 3000, height: int = 4000) -> np.ndarray:
    """Simula foto de celular de un comprobante (resolución alta)."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
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

    y = 100
    for text, f in lines:
        draw.text((80, y), text, fill="black", font=f)
        y += 120

    return img


def resize_image(img: Image.Image, max_dim: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    ratio = max_dim / max(w, h)
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def bench():
    reader = easyocr.Reader(["es"], gpu=False, verbose=False)
    img = create_large_receipt()
    print(f"Imagen original: {img.size[0]}x{img.size[1]}")

    configs = [
        {"name": "Default (canvas=2560)", "canvas_size": 2560, "resize": None},
        {"name": "canvas=1280", "canvas_size": 1280, "resize": None},
        {"name": "Resize 1280 + canvas=1280", "canvas_size": 1280, "resize": 1280},
        {"name": "Resize 1024 + canvas=1024", "canvas_size": 1024, "resize": 1024},
    ]

    for cfg in configs:
        print(f"\n=== {cfg['name']} ===")

        test_img = img
        if cfg["resize"]:
            test_img = resize_image(img, cfg["resize"])
            print(f"  Imagen: {test_img.size[0]}x{test_img.size[1]}")

        img_array = np.array(test_img)

        times = []
        for i in range(3):
            t0 = time.perf_counter()
            result = reader.readtext(img_array, canvas_size=cfg["canvas_size"])
            elapsed = time.perf_counter() - t0
            times.append(elapsed)

        texts = [r[1] for r in result]
        confs = [r[2] for r in result]
        avg_conf = sum(confs) / len(confs) if confs else 0

        print(f"  Promedio: {sum(times)/len(times):.2f}s")
        print(f"  Detecciones: {len(result)}, Confianza: {avg_conf:.2f}")
        print(f"  Texto: {' '.join(texts[:5])}...")


if __name__ == "__main__":
    bench()
