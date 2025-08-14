from fastapi import APIRouter

from betor.services.scrape_service import ScrapeService

from .schemas import ScrapePayload, ScrapeResponse

scrape_router = APIRouter()


@scrape_router.post("/")
async def scrape(payload: ScrapePayload) -> ScrapeResponse:
    service = ScrapeService()
    scrape_return = await service.scrape(deep=payload.deep, q=payload.q)
    return ScrapeResponse(scrape_return=scrape_return)
