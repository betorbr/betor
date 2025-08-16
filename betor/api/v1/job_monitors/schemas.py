from typing import Any, Dict

import scrapy
from pydantic import BaseModel, field_serializer

from betor.entities import Job, JobMonitor


class JobMonitorResponse(BaseModel):
    job_monitor: JobMonitor
    jobs: Dict[str, Job]
    results: Dict[str, Any]

    @field_serializer("results", when_used="json")
    def results_serializer(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            job_index: [self.result_serializer(r) for r in rs]
            for job_index, rs in results.items()
        }

    def result_serializer(self, result: Any) -> Any:
        if isinstance(result, scrapy.Item):
            return dict(result)
        return result
