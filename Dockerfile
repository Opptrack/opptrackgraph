FROM python:3.13-slim

WORKDIR /app
#

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-linux.txt .
RUN pip install --no-cache-dir -r requirements-linux.txt

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

