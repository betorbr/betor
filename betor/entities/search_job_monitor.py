from typing import List, TypedDict

from betor.providers import ProviderSlug

from .job_monitor import Job, JobMonitor


class SearchRequest(TypedDict):
    q: str
    providers_slug: List[ProviderSlug]
    deep: int


class SearchProviderResult(TypedDict):
    job_index: str
    job: Job


class SearchJobMonitor(TypedDict):
    job_monitor: JobMonitor
    providers_result: List[SearchProviderResult]
