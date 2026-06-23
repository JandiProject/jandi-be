from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura

logger = logging.getLogger(__name__)
MAX_REDIRECTS = 5


def validate_crawl_url(url: str) -> str:
    """
    크롤링 대상 URL이 공인 HTTP(S) 주소인지 검증합니다.

    :param url: 검증할 URL.
    :return: 정규화된 URL.
    :raises ValueError: 허용되지 않은 URL이면 발생.
    """
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL hostname is required")

    try:
        addrinfo = socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Failed to resolve hostname") from exc

    for _, _, _, _, sockaddr in addrinfo:
        host = sockaddr[0]
        ip_addr = ipaddress.ip_address(host)
        if (
            ip_addr.is_private
            or ip_addr.is_loopback
            or ip_addr.is_link_local
            or ip_addr.is_multicast
            or ip_addr.is_reserved
            or ip_addr.is_unspecified
        ):
            raise ValueError("Private or non-routable addresses are not allowed")

    return parsed.geturl()


def _fetch_response(url: str) -> httpx.Response:
    """
    redirect를 수동 검증하며 최종 응답을 조회합니다.

    :param url: 조회할 URL.
    :return: 최종 HTTP 응답.
    """
    current_url = validate_crawl_url(url)
    with httpx.Client(timeout=10.0, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            response = client.get(current_url)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise ValueError("Redirect location header is missing")
                current_url = validate_crawl_url(urljoin(current_url, location))
                continue
            response.raise_for_status()
            return response
    raise ValueError("Too many redirects")


def crawl_content(url: str) -> str | None:
    """
    단일 URL의 본문을 크롤링합니다.

    :param url: 크롤링할 페이지 URL.
    :return: 추출된 본문 텍스트 또는 None.
    """
    try:
        response = _fetch_response(url)
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

    TODO: URL 수가 많아질 경우 asyncio/ThreadPoolExecutor로 병렬 처리 전환 고려.
    """
    results = []
    for url in urls:
        content = crawl_content(url)
        results.append({"url": url, "content": content})
    return results
