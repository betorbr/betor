import motor.motor_asyncio
from fastapi import FastAPI, Request


class BetorFastAPI(FastAPI):
    mongodb_client: motor.motor_asyncio.AsyncIOMotorClient


class BetorRequest(Request):
    app: BetorFastAPI
