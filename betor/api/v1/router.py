from fastapi import APIRouter

from .items.router import items_router

router = APIRouter()
router.include_router(items_router, prefix="/items")
