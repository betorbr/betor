class ItemNotFound(Exception):
    pass


class RawItemNotFound(Exception):
    pass


class JobMonitorNotFound(Exception):
    def __init__(self, job_monitor_id: str, *args):
        super().__init__(*args)
        self.job_monitor_id = job_monitor_id
