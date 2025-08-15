import asyncio
from typing import List, Optional, TypedDict

import redis

from betor.entities import Job, JobMonitor
from betor.providers import PROVIDERS, Provider
from betor.repositories import JobMonitorRepository
from betor.use_services import ScrapydScheduleResponse, ScrapydUseService


class ScrapeReturn(TypedDict):
    scrapyd_schedules_response: List[ScrapydScheduleResponse]
    job_monitor: JobMonitor


class ScrapeService:
    def __init__(self, redis_client: redis.Redis):
        self.scrapyd_use_service = ScrapydUseService()
        self.job_monitor_repository = JobMonitorRepository(redis_client)

    async def scrape(self, deep: int = 3, q: Optional[str] = None) -> ScrapeReturn:
        job_monitor = self.job_monitor_repository.create()
        scrapyd_schedules_response = await asyncio.gather(
            *[
                self.scrape_provider_and_add_job(provider, job_monitor, deep, q)
                for provider in PROVIDERS
            ]
        )
        return ScrapeReturn(
            scrapyd_schedules_response=scrapyd_schedules_response,
            job_monitor=job_monitor,
        )

    async def scrape_provider_and_add_job(
        self, provider: Provider, job_monitor: JobMonitor, deep: int, q: Optional[str]
    ) -> ScrapydScheduleResponse:
        scrapyd_schedule_response = await self.scrapyd_use_service.schedule(
            "betor",
            provider.slug,
            deep=deep,
            q=q,
            job_monitor_id=job_monitor["id"],
            job_index=provider.slug,
        )
        self.job_monitor_repository.add_job(
            job_monitor,
            Job(type="scrapd-schedule", id=scrapyd_schedule_response["jobid"]),
            job_index=provider.slug,
        )
        return scrapyd_schedule_response
