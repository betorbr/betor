import logging
from datetime import datetime

from influxdb_client_3 import InfluxDBClient3, Point
from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector, StatsT

logger = logging.getLogger(__name__)


class InfluxDBStatsCollector(StatsCollector):
    def __init__(self, crawler: Crawler) -> None:
        super().__init__(crawler)
        self.influxdb_host = self._crawler.settings.get("INFLUXDB_HOST")
        self.influxdb_org = self._crawler.settings.get("INFLUXDB_ORG")
        self.influxdb_database = self._crawler.settings.get("INFLUXDB_DATABASE")
        self.influxdb_token = self._crawler.settings.get("INFLUXDB_TOKEN")
        self.influxdb_measurement_name = self._crawler.settings.get(
            "INFLUXDB_MEASUREMENT_NAME"
        )
        self.client = InfluxDBClient3(
            host=self.influxdb_host,
            org=self.influxdb_org,
            database=self.influxdb_database,
            token=self.influxdb_token,
        )
        self.spider = None

    def _persist_stats(self, stats: StatsT):
        if not self._crawler.spider:
            logger.warning("Skipping persist stats, spider not setted...")
            return
        point = Point(self.influxdb_measurement_name).tag(
            "spider_name", self._crawler.spider.name
        )
        for key, value in stats.items():
            if isinstance(value, datetime):
                value = value.timestamp()  # noqa: PLW2901
            point = point.field(key, value)
        self.client.write(point)
