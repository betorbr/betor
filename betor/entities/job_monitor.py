from datetime import datetime
from typing import Literal, TypeAlias, TypedDict

JobType: TypeAlias = Literal["scrapd-schedule", "celery-task"]


class JobMonitor(TypedDict):
    id: str
    expired_at: datetime


class Job(TypedDict):
    type: JobType
    id: str
