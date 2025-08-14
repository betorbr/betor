import json
from typing import List, cast
from uuid import uuid4

import redis

from betor.entities import Job, JobMonitor


class JobMonitorRepository:
    @classmethod
    def redis_key(cls, job_id: str) -> str:
        return f"job_{job_id}"

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def create(self, *jobs: Job) -> JobMonitor:
        job_id = str(uuid4())
        key = JobMonitorRepository.redis_key(job_id)
        self.redis_client.lpush(key, *[json.dumps(j) for j in jobs])
        self.redis_client.expire(key, 60 * 60)
        return JobMonitor(id=job_id, jobs=list(jobs))

    def get(self, job_id: str) -> JobMonitor:
        key = JobMonitorRepository.redis_key(job_id)
        jobs_list = cast(List[str], self.redis_client.lrange(key, 0, -1))
        return JobMonitor(
            id=job_id,
            jobs=[json.loads(j) for j in jobs_list],
        )

    def append_job(self, job_id: str, *jobs: Job):
        key = JobMonitorRepository.redis_key(job_id)
        self.redis_client.lpush(key, *[json.dumps(j) for j in jobs])
