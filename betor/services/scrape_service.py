import asyncio
from typing import List, Optional, TypedDict

from betor.providers import PROVIDERS
from betor.use_services import ScrapydScheduleResponse, ScrapydUseService


class ScrapeReturn(TypedDict):
    scrapyd_schedules_response: List[ScrapydScheduleResponse]


class ScrapeService:
    def __init__(self):
        self.scrapyd_use_service = ScrapydUseService()

    async def scrape(self, deep: int = 3, q: Optional[str] = None) -> ScrapeReturn:
        scrapyd_schedules_response = await asyncio.gather(
            *[
                self.scrapyd_use_service.schedule(
                    "betor", provider.slug, deep=deep, q=q
                )
                for provider in PROVIDERS
            ]
        )
        return ScrapeReturn(scrapyd_schedules_response=scrapyd_schedules_response)
