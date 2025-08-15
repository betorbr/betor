from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict


class Job(TypedDict):
    type: Literal["celery-task", "scrapd-job"]
    id: str
    results: Optional[List[Any]]


class JobMonitor(TypedDict):
    id: str
    expired_at: datetime
    jobs: Optional[Dict[str, Job]]
