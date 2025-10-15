FROM python:3.11-slim

# Dependencias del sistema para ocrmypdf + tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa tesseract-ocr-eng \
    ghostscript qpdf unpaper pngquant \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# (Opcional) añade más idiomas: tesseract-ocr-fra, -deu, etc.

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]