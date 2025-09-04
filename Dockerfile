# Dockerfile
FROM python:3.11-slim

# QoL envs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

# Install deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Switch to non-root
USER appuser

# Optional (docs only): Render will map the real port via $PORT
EXPOSE 8000

# IMPORTANT: bind to $PORT on Render, fall back to 8000 locally
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

