from typing import Callable

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from betor.api.fast_api import BetorFastAPI
from betor.repositories.items_repository import ItemsRepository


def collect_items_metrics(
    app: BetorFastAPI, instrumentator: Instrumentator
) -> Callable[..., None]:
    METRIC_TOTAL = Gauge(
        "betor_items_count_total",
        "Number of items by provider and type",
        ["provider_slug", "item_type"],
        registry=instrumentator.registry,
    )

    async def _collect():
        repository = ItemsRepository(app.mongodb_client)
        result = await repository.count_by_provider_slug_and_item_type()
        for (
            provider_slug,
            item_type,
        ), count in result.items():
            METRIC_TOTAL.labels(
                provider_slug=provider_slug, item_type=(item_type or "unknown")
            ).set(count)

    return _collect
