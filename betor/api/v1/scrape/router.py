from fastapi import APIRouter

from betor.api.fast_api import BetorRequest
from betor.services.scrape_service import ScrapeService

from .schemas import ScrapePayload, ScrapeResponse

scrape_router = APIRouter()


@scrape_router.post("/")
async def scrape(request: BetorRequest, payload: ScrapePayload) -> ScrapeResponse:
    service = ScrapeService(request.app.redis_client)
    scrape_return = await service.scrape(deep=payload.deep, q=payload.q)
    return ScrapeResponse(scrape_return=scrape_return)
