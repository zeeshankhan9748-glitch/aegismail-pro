from celery import Celery

from worker_app.settings import get_worker_settings

settings = get_worker_settings()

celery_app = Celery('aegismail_worker', broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=5,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)
celery_app.autodiscover_tasks(['worker_app'])
