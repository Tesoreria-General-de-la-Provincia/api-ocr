# API OCR

REST API para extraccion de texto de imagenes y PDFs usando EasyOCR.

## Stack

- **FastAPI** + **Uvicorn** - API framework
- **EasyOCR** - Motor OCR (CPU-only, ~500MB RAM)
- **PyMuPDF** - Extraccion de texto digital de PDFs
- **UV** - Package manager
- **Docker Compose** - Deployment

## Funcionalidades

- OCR de imagenes (JPG, PNG, WebP)
- OCR de PDFs escaneados (1 pagina)
- Extraccion directa de texto digital en PDFs (sin OCR)
- Resize automatico de imagenes para optimizar velocidad
- Documentacion interactiva con Scalar UI

## Requisitos

- Python 3.12+
- [UV](https://docs.astral.sh/uv/)
- Docker y Docker Compose (para deployment)

## Setup local

```bash
# Instalar dependencias
uv sync

# Copiar variables de entorno
cp .env.example .env

# Levantar el servidor
uv run uvicorn app.main:app --reload
```

La API estara disponible en `http://localhost:8000`. La raiz redirige a `/scalar` (documentacion).

## Docker

```bash
# Copiar variables de entorno
cp .env.example .env

# Build y run
docker compose up --build
```

Para desarrollo con hot reload, en `.env` descomentar `APP_RELOAD=true`.

## Endpoints

### `POST /ocr`

Extrae texto de una imagen o PDF.

**Request:** `multipart/form-data` con campo `file`

**Response:**

```json
{
  "success": true,
  "data": {
    "text": "Texto extraido del documento...",
    "confidence": 0.89,
    "source_type": "ocr",
    "pages": 1,
    "language_detected": "es"
  }
}
```

- `source_type`: `"ocr"` si uso OCR, `"pdf_text"` si extrajo texto digital
- `confidence`: 0-1, promedio de confianza del OCR (1.0 para texto digital)

### `GET /health`

Health check. Reporta si el modelo OCR esta cargado.

### `GET /`

Redirige a `/scalar` (documentacion interactiva).

## Variables de entorno

| Variable             | Default | Descripcion                                  |
| -------------------- | ------- | -------------------------------------------- |
| `APP_PORT`           | `8000`  | Puerto de la API                             |
| `LOG_LEVEL`          | `INFO`  | Nivel de logging                             |
| `OCR_LANG`           | `es`    | Idioma del OCR                               |
| `OCR_MAX_DIMENSION`  | `1024`  | Max px para resize antes de OCR              |
| `MEMORY_LIMIT`       | `2G`    | Limite de memoria Docker                     |
| `MEMORY_RESERVATION` | `1G`    | Reserva de memoria Docker                    |
| `APP_RELOAD`         | -       | Si tiene valor, activa `--reload` en uvicorn |

## Estructura

```bash
api-ocr/
├── app/
│   ├── main.py              # FastAPI app + Scalar UI
│   ├── api/routes/ocr.py    # POST /ocr endpoint
│   ├── core/config.py       # Settings (pydantic-settings)
│   ├── services/ocr_service.py  # Logica OCR
│   └── schemas/ocr.py       # Modelos Pydantic
├── tests/
├── docker/Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Performance

Benchmarks en CPU (Apple Silicon):

| Escenario                   | Tiempo              |
| --------------------------- | ------------------- |
| Carga inicial del modelo    | ~53s (una sola vez) |
| Imagen simple (800x200)     | ~0.3s               |
| Comprobante bancario (foto) | ~3-7s               |

El modelo se precarga al iniciar la app. La primera request no sufre el delay de carga.
