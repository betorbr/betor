import motor.motor_asyncio
import redis
from fastapi import FastAPI, Request


class BetorFastAPI(FastAPI):
    mongodb_client: motor.motor_asyncio.AsyncIOMotorClient
    redis_client: redis.Redis


class BetorRequest(Request):
    app: BetorFastAPI
