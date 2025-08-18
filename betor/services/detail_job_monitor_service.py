from typing import Dict, List, TypedDict

import redis

from betor.entities import Job, JobMonitor
from betor.repositories import JobMonitorRepository

from .get_job_status_service import GetJobStatusService, JobStatus


class JobMonitorDetails(TypedDict):
    job_monitor: JobMonitor
    jobs: Dict[str, Job]
    results: Dict[str, List]
    status: Dict[str, JobStatus]


class DetailJobMonitorService:
    def __init__(self, redis_client: redis.Redis):
        self.job_monitor_repository = JobMonitorRepository(redis_client)
        self.get_job_status_service = GetJobStatusService()

    async def detail(self, job_monitor_id: str) -> JobMonitorDetails:
        job_monitor = self.job_monitor_repository.get(job_monitor_id)
        jobs = self.job_monitor_repository.get_jobs(job_monitor_id)
        results = {
            job_index: self.job_monitor_repository.get_results(
                job_monitor["id"], job_index
            )
            for job_index in jobs.keys()
        }
        status = {
            job_index: await self.get_job_status_service.get(job)
            for job_index, job in jobs.items()
        }
        return JobMonitorDetails(
            job_monitor=job_monitor,
            jobs=jobs,
            results=results,
            status=status,
        )
