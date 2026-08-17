FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1             PYTHONUNBUFFERED=1

WORKDIR /workspace/apps/worker

COPY apps/worker/pyproject.toml apps/worker/README.md ./
COPY apps/worker/worker_app ./worker_app
COPY apps/api/app /workspace/apps/api/app

RUN pip install --no-cache-dir --upgrade pip &&             pip install --no-cache-dir .

CMD ["celery", "-A", "worker_app.celery_app", "worker", "--loglevel=info"]
