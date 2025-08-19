from typing import Generic, TypeVar

from fastapi_pagination import Page

from betor.entities import JobMonitor

T = TypeVar("T")


class SearchPage(Generic[T], Page[T]):
    q: str
    job_monitor: JobMonitor
