from fastapi import APIRouter

from .admin.router import admin_router
from .catalog.router import catalog_router
from .items.router import items_router
from .job_monitors.router import job_monitors_router
from .scrape.router import scrape_router
from .search.router import search_router

router = APIRouter()
router.include_router(items_router, prefix="/items")
router.include_router(scrape_router, prefix="/scrape")
router.include_router(job_monitors_router, prefix="/job-monitors")
router.include_router(search_router, prefix="/search")
router.include_router(catalog_router, prefix="/catalog")
router.include_router(admin_router, prefix="/admin")
