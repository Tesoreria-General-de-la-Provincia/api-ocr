FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para PaddleOCR y PyMuPDF
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo pyproject.toml primero para caching
COPY app/pyproject.toml ./pyproject.toml

# Instalar uv
RUN pip install uv

# Instalar dependencias Python
RUN uv pip install --system --index-url https://pypi.org/simple/ \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    python-multipart>=0.0.9 \
    paddlepaddle>=3.0.0 \
    paddleocr>=3.0.0 \
    pymupdf>=1.25.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    scalar-fastapi>=1.0.0

# Copiar código de la app
COPY app/ ./app/

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV OCR_LANG=es
ENV LOG_LEVEL=INFO

EXPOSE 8000

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
