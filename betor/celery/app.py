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
    Queue("api-requests"),
]
celery_app.conf.task_routes = {
    "process_raw_item": {"queue": "items"},
    "update_item_languages_info": {"queue": "items"},
    "update_item_episodes_info": {"queue": "items"},
    "update_item_torrent_info": {"queue": "torrents"},
    "tmdb_api_request": {"queue": "api-requests"},
    "update_item_torrent_trackers_info": {"queue": "torrents"},
}
