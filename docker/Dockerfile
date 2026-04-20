FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependencias del sistema para EasyOCR y PyMuPDF
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias para cache de layers
COPY pyproject.toml uv.lock ./

# Instalar solo dependencias (sin el proyecto, para cachear este layer)
RUN uv sync --frozen --no-dev --no-install-project

# Copiar código de la app e instalar el proyecto
COPY app/ ./app/

RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1
ENV OCR_LANG=es
ENV LOG_LEVEL=INFO

EXPOSE 8000

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
