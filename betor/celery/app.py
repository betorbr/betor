from celery import Celery
from kombu import Queue

from betor.settings import celery_settings

celery_app = Celery(
    "tasks",
    broker=celery_settings.broker_url,
    backend=celery_settings.backend_url,
    include=["betor.celery.tasks"],
)
celery_app.conf.task_queues = [
    Queue("items"),
    Queue("torrents"),
]
celery_app.conf.task_routes = {
    "process_raw_item": {"queue": "items"},
    "update_item_torrent_info": {"queue": "torrents"},
}
