import redis

from betor.repositories import JobMonitorRepository


class AddJobResultsService:
    def __init__(self, redis_client: redis.Redis):
        self.job_monitor_repository = JobMonitorRepository(redis_client)

    def add(self, job_monitor_id: str, job_index: str, *results):
        self.job_monitor_repository.add_result(job_monitor_id, job_index, *results)
