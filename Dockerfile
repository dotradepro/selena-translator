FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git tar ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY web ./web

ENV HELSINKI_OUT_DIR=/app/data/helsinki-out \
    HF_HOME=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://localhost:8002/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
