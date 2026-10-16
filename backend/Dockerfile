FROM python:3.12-slim AS base
WORKDIR /app

# Install dependencies first for layer caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app/ ./app/

# Create nonroot user
RUN adduser --disabled-password --gecos "" lumen && \
    chown -R lumen:lumen /app
USER lumen

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import httpx; r=httpx.get('http://127.0.0.1:8000/api/v1/health'); exit(0 if r.status_code==200 else 1)" || exit 1

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]