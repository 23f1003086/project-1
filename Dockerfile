FROM python:3.11-slim

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    git \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
USER appuser
WORKDIR /app

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

EXPOSE 7860

CMD ["python", "app.py"]
