from celery import Celery

from betor.settings import celery_settings

celery_app = Celery(
    "tasks", broker=celery_settings.broker_url, backend=celery_settings.backend_url
)
