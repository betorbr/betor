import motor.motor_asyncio
import redis
from apscheduler.schedulers.base import BaseScheduler
from fastapi import FastAPI, Request


class BetorFastAPI(FastAPI):
    mongodb_client: motor.motor_asyncio.AsyncIOMotorClient
    redis_client: redis.Redis
    scheduler: BaseScheduler


class BetorRequest(Request):
    app: BetorFastAPI
