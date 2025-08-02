import motor.motor_asyncio

from betor.settings import database_mongodb_settings


def get_mongodb_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(
        database_mongodb_settings.connection_uri
    )
