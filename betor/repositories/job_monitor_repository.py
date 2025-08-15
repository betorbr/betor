import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from uuid import uuid4

import redis

from betor.entities import Job, JobMonitor


class JobMonitorNotFound(Exception):
    def __init__(self, job_monitor_id: str, *args):
        super().__init__(*args)
        self.job_monitor_id = job_monitor_id


class JobMonitorRepository:
    @classmethod
    def redis_job_monitor_key(cls, job_monitor_id: str) -> str:
        return f"job_monitor:{job_monitor_id}"

    @classmethod
    def redis_jobs_key(cls, job_monitor_id: str) -> str:
        return f"{JobMonitorRepository.redis_job_monitor_key(job_monitor_id)}:jobs"

    @classmethod
    def redis_job_result_key(cls, job_monitor_id: str, job_index: str) -> str:
        return f"{JobMonitorRepository.redis_job_monitor_key(job_monitor_id)}:{job_index}:results"

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def create(self) -> JobMonitor:
        job_monitor_id = str(uuid4())
        expired_at = datetime.now() + timedelta(hours=2)
        key = JobMonitorRepository.redis_job_monitor_key(job_monitor_id)
        job_monitor = JobMonitor(id=job_monitor_id, expired_at=expired_at, jobs=None)
        self.redis_client.set(
            key,
            json.dumps(
                {"id": job_monitor["id"], "ea": job_monitor["expired_at"].timestamp()}
            ),
            exat=int(expired_at.timestamp()),
        )
        return job_monitor

    def get(self, job_monitor_id: str, deep: bool = False) -> JobMonitor:
        key = JobMonitorRepository.redis_job_monitor_key(job_monitor_id)
        value = cast(str, self.redis_client.get(key))
        if not value:
            raise JobMonitorNotFound(job_monitor_id)
        data = cast(dict, json.loads(value))
        job_monitor = JobMonitor(
            id=data["id"],
            expired_at=datetime.fromtimestamp(data["ea"]),
            jobs=None,
        )
        if deep:
            jobs_key = JobMonitorRepository.redis_jobs_key(job_monitor["id"])
            jobs_raw_data = cast(
                Dict[bytes, bytes], self.redis_client.hgetall(jobs_key)
            )
            job_monitor["jobs"] = {
                k.decode(): Job(  # type: ignore[typeddict-item]
                    results=self._get_results(job_monitor_id, k.decode()),
                    **json.loads(v),
                )
                for k, v in jobs_raw_data.items()
            }
        return job_monitor

    def add_job(
        self,
        job_monitor: Union[str, JobMonitor],
        job: Job,
        job_index: Optional[str] = None,
    ) -> str:
        job_monitor = (
            self.get(job_monitor) if isinstance(job_monitor, str) else job_monitor
        )
        job_index = job_index or str(uuid4())
        key = JobMonitorRepository.redis_jobs_key(job_monitor["id"])
        self.redis_client.hset(key, job_index, json.dumps(job))
        self.redis_client.expireat(key, int(job_monitor["expired_at"].timestamp()))
        return job_index

    def add_result(self, job_monitor: Union[str, JobMonitor], job_index: str, *results):
        job_monitor = (
            self.get(job_monitor) if isinstance(job_monitor, str) else job_monitor
        )
        key = JobMonitorRepository.redis_job_result_key(job_monitor["id"], job_index)
        self.redis_client.lpush(key, *[json.dumps(r) for r in results])
        self.redis_client.expireat(key, int(job_monitor["expired_at"].timestamp()))

    def _get_results(self, job_monitor_id: str, job_index: str) -> List[Any]:
        key = JobMonitorRepository.redis_job_result_key(job_monitor_id, job_index)
        results = cast(List[bytes], self.redis_client.lrange(key, 0, -1))
        return [json.loads(r) for r in results]
