from celery import Celery

from app.settings import get_settings

settings = get_settings()

celery_client = Celery("aegismail_api", broker=settings.redis_url, backend=settings.redis_url)


def enqueue_send_email(message_id: int) -> None:
    celery_client.send_task("worker_app.tasks.send_email_task", args=[message_id])
