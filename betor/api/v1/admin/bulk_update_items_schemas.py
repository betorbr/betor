from typing import List

from pydantic import BaseModel, Field


class BulkUpdateItemsRequest(BaseModel):
    """Request payload for bulk update items endpoint."""

    limit: int = Field(default=50, ge=1, le=1000, description="Max items to process")
    exclude_updated_within_days: int = Field(
        default=30,
        ge=0,
        description="Exclude items updated within X days",
    )


class BulkUpdateItemsResponse(BaseModel):
    """Response payload for bulk update items endpoint."""

    task_ids: List[str] = Field(description="UUIDs of dispatched Celery tasks")
    processed_count: int = Field(description="Number of items scheduled for update")
    excluded_count: int = Field(description="Number of items excluded by date filter")
    total_available: int = Field(
        description="Total items without date filter (respecting limit)"
    )
