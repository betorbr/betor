import hashlib
import pickle
from typing import Optional, cast

import redis

from betor.entities import SearchJobMonitor, SearchRequest
from betor.settings import search_job_monitor_settings


class SearchJobMonitorRepository:
    @classmethod
    def redis_key(self, search_request: SearchRequest) -> str:
        hash_object = hashlib.sha256(
            f"{search_request['q']}-{search_request['providers_slug']}-{search_request['deep']}".encode()
        )
        return f"search_job_monitor:{hash_object.hexdigest()}"

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def get(self, search_request: SearchRequest) -> Optional[SearchJobMonitor]:
        key = SearchJobMonitorRepository.redis_key(search_request)
        if search_job_monitor_raw := cast(bytes, self.redis_client.get(key)):
            return cast(SearchJobMonitor, pickle.loads(search_job_monitor_raw))
        return None

    def set(self, search_request: SearchRequest, search_job_monitor: SearchJobMonitor):
        key = SearchJobMonitorRepository.redis_key(search_request)
        self.redis_client.set(
            key, pickle.dumps(search_job_monitor), ex=search_job_monitor_settings.ttl
        )
