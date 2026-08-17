from celery.utils.log import get_task_logger

from worker_app.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=5)
def send_test_email(self, provider_id: int, recipient: str) -> dict[str, str | int]:
    logger.info('queued test email task', extra={'provider_id': provider_id, 'recipient': recipient})
    return {
        'status': 'queued-for-phase-2',
        'provider_id': provider_id,
        'recipient': recipient,
        'message': 'SMTP delivery execution will be implemented in a later phase.',
    }


@celery_app.task
def ping_task() -> dict[str, str]:
    return {'status': 'ok', 'message': 'worker reachable'}
