# AegisMail Pro Worker

Celery worker scaffold for queue-oriented work.

- Broker: `REDIS_URL`
- Example task: `send_test_email`
- Retry strategy: exponential backoff with bounded retries

## Graceful shutdown
Celery handles `SIGTERM`/`SIGINT` gracefully by finishing in-flight acknowledgements before worker exit when run with the default prefork worker. For local development, stop the worker with `Ctrl+C` and wait for Celery to drain current work before the container exits.

## Local commands
```bash
pip install -e .
celery -A worker_app.celery_app worker --loglevel=info
```
