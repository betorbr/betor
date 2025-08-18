from typing import Literal, TypeAlias

import celery.result

from betor.entities import Job
from betor.use_services import ScrapydUseService

JobStatus: TypeAlias = Literal["unknown", "waiting", "running", "success", "fail"]


class GetJobStatusService:
    def __init__(self):
        self.scrapyd_use_service = ScrapydUseService()

    async def get(self, job: Job) -> JobStatus:
        if job["type"] == "scrapd-schedule":
            return await self.get_scrapd_schedule(job)
        if job["type"] == "celery-task":
            return await self.get_celery_task(job)
        raise NotImplementedError()

    async def get_scrapd_schedule(self, job: Job) -> JobStatus:
        job_status = await self.scrapyd_use_service.status(job["id"])
        if job_status["currstate"] == "pending":
            return "waiting"
        if job_status["currstate"] == "running":
            return "running"
        if job_status["currstate"] == "finished":
            return "success"
        return "unknown"

    async def get_celery_task(self, job: Job) -> JobStatus:
        result = celery.result.AsyncResult(job["id"])
        state = result.state
        if state == "PENDING":
            return "waiting"
        if state == "STARTED":
            return "running"
        if state == "RETRY":
            return "running"
        if state == "FAILURE":
            return "fail"
        if state == "SUCCESS":
            return "success"
        return "unknown"
