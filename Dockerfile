FROM python:3.13-slim

WORKDIR /app
#

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    tesseract-ocr \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set build-time ARG and runtime ENV for NLTK
ARG NLTK_DATA_PATH=/usr/share/nltk_data
ENV NLTK_DATA=$NLTK_DATA_PATH

# Install Python dependencies
COPY requirements-linux.txt .
RUN pip install --no-cache-dir -r requirements-linux.txt

# Download NLTK data to the specified path
RUN mkdir -p /usr/share/nltk_data && \
    python -m nltk.downloader -d /usr/share/nltk_data \
        punkt \
        punkt_tab \
        averaged_perceptron_tagger \
        averaged_perceptron_tagger_eng \
        maxent_ne_chunker \
        maxent_ne_chunker_tab \
        words

# Copy application code
COPY . .

# Set up logs and permissions
RUN mkdir -p /app/logs && \
    touch /app/logs/app.log && \
    useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

