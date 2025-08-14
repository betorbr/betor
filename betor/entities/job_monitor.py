from typing import List, Literal, TypeAlias, TypedDict, Union


class CeleryTaskJob(TypedDict):
    type: Literal["celery-task"]
    task_uuid: str


class ScrapydJob(TypedDict):
    type: Literal["scrapd-job"]
    job_id: str


Job: TypeAlias = Union[CeleryTaskJob, ScrapydJob]


class JobMonitor(TypedDict):
    id: str
    jobs: List[Job]
