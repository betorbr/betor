from fastapi import APIRouter, HTTPException, status

from betor.api.fast_api import BetorRequest
from betor.repositories import JobMonitorNotFound
from betor.services import DetailJobMonitorService

from .schemas import JobMonitorResponse

job_monitors_router = APIRouter()


@job_monitors_router.get("/{job_monitor_id}/")
async def detail_job_monitor(
    request: BetorRequest, job_monitor_id: str
) -> JobMonitorResponse:
    service = DetailJobMonitorService(request.app.redis_client)
    try:
        details = await service.detail(job_monitor_id)
    except JobMonitorNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job Monitor not found")
    return JobMonitorResponse(
        job_monitor=details["job_monitor"],
        jobs=details["jobs"],
        results=details["results"],
    )
