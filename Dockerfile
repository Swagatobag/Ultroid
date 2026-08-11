# Minimal Dockerfile for Ultroid (Python Telethon bot)
FROM python:3.11-slim

# Install system deps needed by ffmpeg and some Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      gcc \
      libffi-dev \
      libssl-dev \
      build-essential \
      git \
      libpq-dev \
      && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt resources/startup/optional-requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && if [ -f resources/startup/optional-requirements.txt ]; then pip install --no-cache-dir -r resources/startup/optional-requirements.txt || true; fi

# Copy the rest of the repo
COPY . .

# Use python module entrypoint used in README/startup
CMD ["python", "-m", "pyUltroid"]
