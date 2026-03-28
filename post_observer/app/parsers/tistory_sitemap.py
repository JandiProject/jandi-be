from __future__ import annotations

import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _parse_lastmod(raw_value: str) -> datetime | None:
    """
    sitemap lastmod 값을 datetime으로 파싱합니다.

    :param raw_value: raw lastmod 문자열.
    :return: datetime 또는 None.
    """
    normalized = raw_value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    for candidate in (normalized, normalized[:19], normalized[:10]):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


class TistorySitemapParser:
    """티스토리 sitemap 기반 전체 글 URL 파서."""

    def get_sitemap_url(self, account_id: str) -> str:
        """
        티스토리 sitemap URL을 반환합니다.

        :param account_id: 티스토리 블로그 ID.
        :return: sitemap URL.
        """
        return f"https://{account_id}.tistory.com/sitemap.xml"

    def parse(self, account_id: str) -> list[dict]:
        """
        sitemap을 파싱하여 전체 글 URL과 발행일 목록을 반환합니다.

        :param account_id: 티스토리 블로그 ID.
        :return: [{"url": ..., "published_at": ...}, ...] 목록.
        """
        sitemap_url = self.get_sitemap_url(account_id)
        logger.info(f"Fetching sitemap: {sitemap_url}")

        try:
            response = httpx.get(sitemap_url, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch sitemap for {account_id}: {e}")
            return []

        soup = BeautifulSoup(response.content, "xml")
        urls = []

        for loc in soup.find_all("url"):
            url_tag = loc.find("loc")
            lastmod_tag = loc.find("lastmod")

            if url_tag is None:
                continue

            url = url_tag.text.strip()

            published_at = None
            if lastmod_tag:
                published_at = _parse_lastmod(lastmod_tag.text)

            urls.append({"url": url, "published_at": published_at})

        logger.info(f"Found {len(urls)} URLs in sitemap for {account_id}")
        return urls
