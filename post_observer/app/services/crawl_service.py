from __future__ import annotations

import logging

import httpx
import trafilatura

logger = logging.getLogger(__name__)


def crawl_content(url: str) -> str | None:
    """
    단일 URL의 본문을 크롤링합니다.

    :param url: 크롤링할 페이지 URL.
    :return: 추출된 본문 텍스트 또는 None.
    """
    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_precision=True,
        )
        return content
    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return None


def crawl_contents(urls: list[str]) -> list[dict]:
    """
    여러 URL의 본문을 순차적으로 크롤링합니다.

    :param urls: 크롤링할 URL 목록.
    :return: [{"url": ..., "content": ...}, ...] 목록.
    """
    results = []
    for url in urls:
        content = crawl_content(url)
        results.append({"url": url, "content": content})
    return results
