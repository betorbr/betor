import asyncio
import itertools
from typing import Dict, Iterable, List, Optional, TypedDict, cast
from uuid import uuid4

import motor.motor_asyncio
import redis

from betor.entities import (
    Item,
    Job,
    JobMonitor,
    SearchJobMonitor,
    SearchProviderResult,
    SearchRequest,
)
from betor.enums import ItemsSortEnum, ItemType
from betor.providers import PROVIDERS, ProviderSlug
from betor.repositories import (
    ItemsRepository,
    JobMonitorRepository,
    SearchJobMonitorRepository,
)
from betor.services.process_raw_item_service import ProcessRawItemReturn
from betor.types import ApaginateParams
from betor.use_services import ScrapydUseService

from .get_job_status_service import GetJobStatusService
from .list_items_service import ListItemsService


class SearchResult(TypedDict):
    q: str
    deep: int
    job_monitor: JobMonitor
    providers_result: List[SearchProviderResult]
    processed_items: List[Item]
    apaginate_params: ApaginateParams


class SearchService:
    def __init__(
        self,
        mongodb_client: motor.motor_asyncio.AsyncIOMotorClient,
        redis_client: redis.Redis,
    ):
        self.job_monitor_repository = JobMonitorRepository(redis_client)
        self.items_repository = ItemsRepository(mongodb_client)
        self.search_job_monitor_repository = SearchJobMonitorRepository(redis_client)
        self.get_job_status_service = GetJobStatusService()
        self.scrapyd_use_service = ScrapydUseService()
        self.list_items_service = ListItemsService(mongodb_client)

    async def search(
        self,
        q: str,
        sort: ItemsSortEnum,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[str] = None,
        item_types: Optional[List[ItemType]] = None,
        providers_slug: Optional[List[ProviderSlug]] = None,
        deep: int = 3,
        scrape_timeout: int = 30,
        process_raw_item_timeout: int = 15,
    ) -> SearchResult:
        search_job_monitor = await self.request_search(q, providers_slug, deep)
        try:
            async with asyncio.timeout(scrape_timeout):
                await self.waiting_completed(
                    [result["job"] for result in search_job_monitor["providers_result"]]
                )
        except asyncio.TimeoutError:
            pass
        try:
            async with asyncio.timeout(process_raw_item_timeout):
                jobs = await self.get_process_raw_item_jobs(
                    search_job_monitor["job_monitor"]["id"]
                )
                await self.waiting_completed(jobs.values())
        except asyncio.TimeoutError:
            pass
        processed_items = await self.get_processed_items(
            search_job_monitor["job_monitor"]["id"]
        )
        return SearchResult(
            q=q,
            deep=deep,
            job_monitor=search_job_monitor["job_monitor"],
            providers_result=search_job_monitor["providers_result"],
            processed_items=processed_items,
            apaginate_params=self.list_items_service.apaginate_params(
                sort,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                item_types=item_types,
                items_id=[i["id"] for i in processed_items if i["id"]],
            ),
        )

    async def request_search(
        self, q: str, providers_slug: Optional[List[ProviderSlug]], deep: int
    ) -> SearchJobMonitor:
        search_request = SearchRequest(
            q=q,
            providers_slug=(
                providers_slug
                if providers_slug is not None
                else cast(List[ProviderSlug], [p.slug for p in PROVIDERS])
            ),
            deep=deep,
        )
        if search_job_monitor := self.search_job_monitor_repository.get(search_request):
            return search_job_monitor
        job_monitor = self.job_monitor_repository.create()
        providers_result = await asyncio.gather(
            *[
                self.search_provider_slug(
                    search_request["q"],
                    search_request["deep"],
                    provider_slug,
                    job_monitor,
                )
                for provider_slug in search_request["providers_slug"]
            ]
        )
        search_job_monitor = SearchJobMonitor(
            job_monitor=job_monitor, providers_result=providers_result
        )
        self.search_job_monitor_repository.set(search_request, search_job_monitor)
        return search_job_monitor

    async def search_provider_slug(
        self, q: str, deep: int, provider_slug: str, job_monitor: JobMonitor
    ) -> SearchProviderResult:
        job_index = str(uuid4())
        scrapyd_schedule_response = await self.scrapyd_use_service.schedule(
            "betor",
            provider_slug,
            q=q,
            deep=deep,
            job_monitor_id=job_monitor["id"],
            job_index=job_index,
        )
        job = Job(
            type="scrapd-schedule",
            name=provider_slug,
            id=scrapyd_schedule_response["jobid"],
        )
        self.job_monitor_repository.add_job(job_monitor, job, job_index=job_index)
        return SearchProviderResult(job_index=job_index, job=job)

    async def waiting_completed(self, jobs: Iterable[Job]):
        while True:
            jobs_status = [await self.get_job_status_service.get(j) for j in jobs]
            if not set(jobs_status) - {"success", "fail"}:
                break
            await asyncio.sleep(0.5)

    async def get_process_raw_item_jobs(self, job_monitor_id: str) -> Dict[str, Job]:
        return {
            job_index: job
            for job_index, job in self.job_monitor_repository.get_jobs(
                job_monitor_id
            ).items()
            if job["name"] == "process_raw_item"
        }

    async def get_processed_items(self, job_monitor_id) -> List[Item]:
        process_raw_item_jobs = await self.get_process_raw_item_jobs(job_monitor_id)
        return list(
            itertools.chain(
                *[
                    itertools.chain(
                        *[
                            cast(ProcessRawItemReturn, r)["items"]
                            for r in self.job_monitor_repository.get_results(
                                job_monitor_id, job_index
                            )
                        ]
                    )
                    for job_index in process_raw_item_jobs.keys()
                ]
            )
        )
