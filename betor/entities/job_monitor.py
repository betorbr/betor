from datetime import datetime
from typing import Literal, TypedDict


class JobMonitor(TypedDict):
    id: str
    expired_at: datetime


class Job(TypedDict):
    type: Literal["scrapd-schedule", "celery-task"]
    id: str
