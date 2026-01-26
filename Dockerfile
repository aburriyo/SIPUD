# ============================================
# SIPUD - Dockerfile de Produccion
# Flask + Gunicorn
# ============================================

FROM python:3.12-slim AS base

# Evitar prompts interactivos y bytecode cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente
COPY . .

# Crear usuario no-root para seguridad
RUN addgroup --system sipud && \
    adduser --system --ingroup sipud sipud && \
    chown -R sipud:sipud /app

USER sipud

# Exponer puerto de Gunicorn
EXPOSE 5006

# Comando por defecto: Gunicorn con 4 workers
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5006", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "run:app"]
