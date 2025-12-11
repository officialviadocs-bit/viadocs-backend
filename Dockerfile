# ===============================================
# VIADOCS Backend - Final Stable Dockerfile
# ===============================================

FROM python:3.11-slim

# --- Install system tools ---
RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    qpdf \
    g++ \
    build-essential \
    libxml2 \
    libxslt1.1 \
    fonts-dejavu-core \
    fonts-liberation \
    imagemagick \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# --- Environment setup ---
ENV PYTHONUNBUFFERED=1
ENV LIBREOFFICE_HEADLESS=true
ENV DEBIAN_FRONTEND=noninteractive

# --- Set working directory ---
WORKDIR /app

# --- Copy only requirements first (caching layer) ---
COPY requirements.txt .

# --- Install Python packages ---
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Copy project files ---
COPY . .

# --- Expose port (Render/Railway use $PORT) ---
EXPOSE 5000

# --- Health check (optional) ---
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-5000}/ || exit 1

# --- Start Gunicorn ---
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300
