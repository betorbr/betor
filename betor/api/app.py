from fastapi_pagination import add_pagination

from betor.databases.mongodb import get_mongodb_client

from .fast_api import BetorFastAPI
from .v1.router import router as router_v1


async def lifespan(app: BetorFastAPI):
    app.mongodb_client = get_mongodb_client()
    yield
    app.mongodb_client.close()


app = BetorFastAPI(lifespan=lifespan)
add_pagination(app)
app.include_router(router_v1, prefix="/v1")
