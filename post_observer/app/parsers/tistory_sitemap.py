from __future__ import annotations

import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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
                try:
                    published_at = datetime.fromisoformat(lastmod_tag.text.strip()[:10])
                except ValueError:
                    pass

            urls.append({"url": url, "published_at": published_at})

        logger.info(f"Found {len(urls)} URLs in sitemap for {account_id}")
        return urls
