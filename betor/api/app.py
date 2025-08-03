from fastapi import FastAPI

from .v1.router import router as router_v1

app = FastAPI()
app.include_router(router_v1, prefix="/v1")
