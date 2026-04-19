from typing import Callable

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from betor.api.fast_api import BetorFastAPI
from betor.repositories.items_repository import ItemsRepository


def collect_items_metrics(
    app: BetorFastAPI, instrumentator: Instrumentator
) -> Callable[..., None]:
    items_count_by_type = Gauge(
        "betor_items_count_by_type",
        "Number of items by type",
        ["item_type"],
        registry=instrumentator.registry,
    )

    async def _collect():
        repository = ItemsRepository(app.mongodb_client)
        counts = await repository.count_by_item_type()
        for item_type, count in counts.items():
            items_count_by_type.labels(item_type=(item_type or "unknown")).set(count)

    return _collect
