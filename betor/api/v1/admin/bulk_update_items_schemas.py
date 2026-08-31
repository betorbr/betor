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


class UpdatedItem(BaseModel):
    """Task and item identifiers for a dispatched update."""

    task_id: str = Field(description="UUID of the dispatched Celery task")
    item_id: str = Field(description="ID of the item being updated")


class BulkUpdateItemsResponse(BaseModel):
    """Response payload for bulk update items endpoint."""

    updated_items: List[UpdatedItem] = Field(
        description="Items and task UUIDs dispatched for update"
    )
    processed_count: int = Field(description="Number of items scheduled for update")
    filtered_count: int = Field(description="Number of items updated within the window")
    remaining_count: int = Field(
        description="Number of items still eligible for update"
    )
