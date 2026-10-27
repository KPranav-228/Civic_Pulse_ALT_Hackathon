# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (curl, build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model (or fallback gracefully in code)
RUN python -m spacy download en_core_web_sm || true

# Copy project files
COPY server/ ./server/
COPY prompts/ ./prompts/
COPY seed/ ./seed/
COPY reports/ ./reports/

# Default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATABASE_URL=sqlite:///./civicpulse.db

EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
