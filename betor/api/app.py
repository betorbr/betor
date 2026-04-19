from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi_pagination import add_pagination
from prometheus_fastapi_instrumentator import Instrumentator

from betor.api.business_metrics import collect_items_metrics
from betor.databases.mongodb import get_mongodb_client
from betor.databases.redis import get_redis_client

from .fast_api import BetorFastAPI
from .v1.router import router as router_v1


async def lifespan(app: BetorFastAPI):
    app.mongodb_client = get_mongodb_client()
    app.redis_client = get_redis_client()
    app.scheduler = AsyncIOScheduler()
    app.scheduler.add_job(
        collect_items_metrics(app, instrumentator), "cron", minute="*", second="*/30"
    )
    app.scheduler.start()
    yield
    app.mongodb_client.close()
    app.redis_client.close()
    app.scheduler.shutdown()


app = BetorFastAPI(lifespan=lifespan)
instrumentator = Instrumentator()

add_pagination(app)
instrumentator.instrument(app).expose(app)

app.include_router(router_v1, prefix="/v1")
