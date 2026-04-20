# API OCR - Especificación Técnica

## 1. Overview

**Project**: api-ocr  
**Type**: REST API Service  
**Stack**: FastAPI + UV + Scalar + PaddleOCR PP-OCRv5 Server + Docker Compose  
**Target**: CPU-only server (i7 10th gen, 16GB RAM)  
**Constraint**: ~600MB RAM para OCR, sin GPU  

## 2. Objetivos

- API que recibe archivos (imágenes JPG/PNG o PDFs de 1 hoja)
- Detecta si el PDF tiene texto digital o necesita OCR
- Devuelve el texto extraído con metadata (confidence, idioma)
- Documentación interactiva con Scalar (OpenAPI UI)
- Dockerizado con Docker Compose

## 3. Modelo OCR

**Elegido**: PaddleOCR PP-OCRv5 Server (configuración mixta)

| Componente | Modelo | Disco | RAM |
|------------|--------|-------|-----|
| Detection | PP-OCRv5_mobile_det | 4.7 MB | ~60MB |
| Recognition | PP-OCRv5_server_rec | 81 MB | ~400MB |
| **Total** | | **~86 MB** | **~500-600MB** |

**Accuracy**: ~86% en reconocimiento de texto (PP-OCRv5 Server vs 81% de Mobile)

**Por qué no modelos más potentes**:
- GLM-OCR (94% accuracy): Requiere GPU con ~2GB VRAM
- PaddleOCR-VL-1.5 (94.5%): Requiere GPU
- DeepSeek-OCR: 3B params, requiere +6GB VRAM
- Budget: Sin GPU, solo CPU

## 4. Arquitectura

```
api-ocr/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + Scalar UI
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── ocr.py       # POST /ocr endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Settings
│   ├── services/
│   │   ├── __init__.py
│   │   └── ocr_service.py   # OCR logic
│   └── schemas/
│       ├── __init__.py
│       └── ocr.py           # Pydantic models
├── tests/
│   └── test_ocr.py          # Unit tests
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.dev.yml
├── pyproject.toml
└── README.md
```

## 5. API Endpoints

### POST /ocr

**Descripción**: Extrae texto de una imagen o PDF usando OCR.

**Request**:
- Content-Type: `multipart/form-data`
- Body: `file` (UploadFile) - imagen o PDF

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "text": "Texto extraído del documento...",
    "confidence": 0.864,
    "source_type": "ocr",
    "pages": 1,
    "language_detected": "es"
  }
}
```

**Response** (error):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE",
    "message": "Solo se aceptan imágenes (JPG, PNG) o PDFs"
  }
}
```

### GET /health

**Descripción**: Health check.

**Response**:
```json
{
  "status": "healthy",
  "ocr_model_loaded": true,
  "version": "0.1.0"
}
```

### GET /

**Descripción**: Redirect a documentación Scalar.

**Response**: 307 Redirect to `/scalar`

## 6. Flujo de Procesamiento

```
1. Upload archivo (image/PDF)
2. Si es PDF:
   a. Extraer texto digital (pymupdf)
   b. Si tiene texto suficiente (>50 chars) → retornar directo
   c. Si no tiene o tiene poco → convertir a imagen → OCR
3. Si es imagen → OCR directo
4. Devolver resultado con metadata
```

**Nota**: El paso 2 evita OCR innecesario en PDFs con texto digital, mejorando velocidad.

## 7. Dependencias

```toml
# pyproject.toml
[project]
name = "api-ocr"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "python-multipart>=0.0.9",
    "paddlepaddle>=3.0.0",
    "paddleocr>=3.0.0",
    "pymupdf>=1.25.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    # Dev
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

## 8. Configuración

**Environment Variables**:
| Variable | Default | Descripción |
|----------|---------|-------------|
| `APP_HOST` | `0.0.0.0` | Host de la app |
| `APP_PORT` | `8000` | Puerto |
| `OCR_LANG` | `es` | Idioma OCR |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `MAX_FILE_SIZE` | `10485760` | 10MB en bytes |

## 9. Límites

| Recurso | Límite |
|---------|--------|
| Tamaño archivo | 10 MB |
| Páginas PDF | 1 |
| Timeout OCR | 60s |
| RAM OCR | ~600MB |

## 10. Docker

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema para PaddleOCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos
COPY app/ ./app/

# Instalar UV y dependencias
RUN pip install uv
RUN uv pip install --system -r app/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  api-ocr:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OCR_LANG=es
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 2G
    restart: unless-stopped
```

## 11. Roadmap

- [ ] Estructura del proyecto (`app/`, `tests/`, `docker/`)
- [ ] Docker configuration (`Dockerfile`, `docker-compose.yml`)
- [ ] FastAPI app con Scalar UI (`main.py`)
- [ ] OCR service con PaddleOCR (`services/ocr_service.py`)
- [ ] Endpoint POST /ocr (`api/routes/ocr.py`)
- [ ] Endpoint GET /health
- [ ] Pydantic schemas (`schemas/ocr.py`)
- [ ] Tests unitarios
- [ ] README.md

## 12. Troubleshooting

**PaddleOCR tarda en iniciar**: Es normal, descarga modelos la primera vez (~100MB).

**Out of Memory**: Reducir a PP-OCRv5 mobile_rec si es necesario.

**PDF no se procesa**: Verificar que sea PDF de 1 página, PDFs multipágina no soportados.
