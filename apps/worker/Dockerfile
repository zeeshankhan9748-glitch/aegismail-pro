FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1             PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY worker_app ./worker_app

RUN pip install --no-cache-dir --upgrade pip &&             pip install --no-cache-dir .

CMD ["celery", "-A", "worker_app.celery_app", "worker", "--loglevel=info"]
