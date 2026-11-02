import logging
import re
import time
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
import scrapy
import scrapy.crawler
import scrapy.signals

logger = logging.getLogger(__name__)


class UnlockBludvGateExtension:
    @classmethod
    def from_crawler(
        cls, crawler: scrapy.crawler.Crawler
    ) -> "UnlockBludvGateExtension":
        base_url = crawler.settings.get("FLARESOLVERR_BASE_URL")
        assert base_url, "FLARESOLVERR_BASE_URL must be defined in settings"
        obj = cls(base_url)
        crawler.signals.connect(obj.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=scrapy.signals.spider_closed)
        return obj

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.cached_token: Optional[str] = None

    def spider_opened(self, spider: scrapy.Spider) -> None:
        spider.bludv_unlocker = self  # type: ignore[attr-defined]

    def spider_closed(self, spider: scrapy.Spider) -> None:
        self._destroy_session()

    def _ensure_session(self) -> str:
        if self.session_id:
            return self.session_id
        self.session_id = f"bludv-unlock-session-{int(time.time() * 1000)}"
        try:
            httpx.post(
                f"{self.base_url}/v1",
                json={"cmd": "sessions.create", "session": self.session_id},
                timeout=10,
            )
        except Exception as e:
            logger.debug("Failed to create FlareSolverr session: %s", e)
        return self.session_id

    def _destroy_session(self) -> None:
        if not self.session_id:
            return
        try:
            httpx.post(
                f"{self.base_url}/v1",
                json={"cmd": "sessions.destroy", "session": self.session_id},
                timeout=5,
            )
        except Exception as e:
            logger.debug("Failed to destroy FlareSolverr session: %s", e)
        self.session_id = None
        self.cached_token = None

    def _flaresolverr_get(self, url: str) -> dict:
        session = self._ensure_session()
        response = httpx.post(
            f"{self.base_url}/v1",
            json={"cmd": "request.get", "url": url, "session": session},
            timeout=45,
        )
        response.raise_for_status()
        return response.json().get("solution", {})

    @staticmethod
    def _extract_magnet(html: str) -> Optional[str]:
        match = re.search(r"var\s+u\s*=\s*\"(magnet:\?[^\"]+)\"", html)
        if match:
            return match.group(1)
        fallback = re.search(r'(magnet:\?[^\s"\']+)', html)
        if fallback:
            return fallback.group(1)
        return None

    def _full_resolve_flow(self, gate_url: str) -> Optional[str]:
        solution = self._flaresolverr_get(gate_url)
        html = solution.get("response", "")

        match = re.search(r"href=\"(https://[^\"]+utm_content=([^\"]+))\"", html)
        if not match:
            return None
        partner_url = match.group(1)
        parsed = urlparse(partner_url)
        codes = parse_qs(parsed.query).get("utm_content")
        if not codes:
            return None
        code = codes[0]

        self._flaresolverr_get(partner_url)
        time.sleep(3)
        self._flaresolverr_get(f"https://promobr.online/api/end?code={code}")

        go_solution = self._flaresolverr_get(f"https://promobr.online/go/{code}")
        final_url = go_solution.get("url", "")
        callback_html = go_solution.get("response", "")

        parsed_final = urlparse(final_url)
        tokens = parse_qs(parsed_final.query).get("token")
        if tokens:
            self.cached_token = tokens[0]

        return self._extract_magnet(callback_html)

    def unlock_gate_url(self, gate_url: str, spider: scrapy.Spider) -> Optional[str]:
        parsed_gate = urlparse(gate_url)
        path_parts = parsed_gate.path.split("/")
        ref = path_parts[-1] if path_parts else ""

        if self.cached_token and ref:
            callback_url = f"https://bludvfilmes2.xyz/gate/callback?token={self.cached_token}&ref={ref}"
            try:
                solution = self._flaresolverr_get(callback_url)
                html = solution.get("response", "")
                magnet = self._extract_magnet(html)
                if magnet:
                    return magnet
            except Exception as e:
                logger.debug(
                    "Failed to unlock with cached token: %s. Re-running full flow...", e
                )

        try:
            magnet = self._full_resolve_flow(gate_url)
            if magnet:
                return magnet
        except Exception as e:
            spider.logger.warning("Failed full resolve flow for %s: %s", gate_url, e)
            self._destroy_session()
            try:
                return self._full_resolve_flow(gate_url)
            except Exception as e2:
                spider.logger.error("Retry failed for %s: %s", gate_url, e2)

        return None
