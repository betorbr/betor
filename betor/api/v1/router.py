from fastapi import APIRouter

from .items.router import items_router
from .job_monitors.router import job_monitors_router
from .scrape.router import scrape_router

router = APIRouter()
router.include_router(items_router, prefix="/items")
router.include_router(scrape_router, prefix="/scrape")
router.include_router(job_monitors_router, prefix="/job-monitors")
