from pydantic import BaseModel, Field

from betor.services import ScrapeReturn


class ScrapePayload(BaseModel):
    deep: int = Field(3)


class ScrapeResponse(BaseModel):
    scrape_return: ScrapeReturn
