from fastapi import FastAPI
from fastapi_pagination import add_pagination

from .v1.router import router as router_v1

app = FastAPI()
add_pagination(app)
app.include_router(router_v1, prefix="/v1")
