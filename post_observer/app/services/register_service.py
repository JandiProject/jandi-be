from __future__ import annotations

import logging
from datetime import datetime

from app.dependencies.rabbitmq import publish_messages
from app.parsers.tistory_sitemap import TistorySitemapParser
from app.services import platform_service, rss_service

logger = logging.getLogger(__name__)

_tistory_sitemap_parser = TistorySitemapParser()


def _collect_tistory(account_id: str) -> list[dict]:
    """
    티스토리 sitemap.xml로 전체 글 URL 목록을 수집합니다.

    :param account_id: 티스토리 블로그 ID.
    :return: [{"url": ..., "published_at": ...}, ...] 목록.
    """
    return _tistory_sitemap_parser.parse(account_id)


def _collect_rss(platform_name: str, account_id: str) -> list[dict]:
    """
    RSS 파싱으로 글 목록을 수집합니다. (네이버, 벨로그 전용)

    :param platform_name: 플랫폼 이름 (naver, velog).
    :param account_id: 플랫폼 계정 ID.
    :return: [{"url": ..., "published_at": ...}, ...] 목록.
    """
    articles = rss_service.fetch_rss(platform_name, account_id)
    return [
        {
            "url": article.link,
            "published_at": article.published_at,
        }
        for article in articles
    ]


def register_platform(user_id: str, platform_name: str, account_id: str) -> int:
    """
    플랫폼 등록 시 해당 유저의 기존 글을 수집하고 RabbitMQ new_posts 큐에 발행합니다.

    수집 전략:
    - 티스토리: sitemap.xml로 전체 글 URL 수집
    - 네이버 / 벨로그: RSS 파싱으로 글 목록 수집

    :param user_id: 유저 ID.
    :param platform_name: 플랫폼 이름 (naver, tistory, velog).
    :param account_id: 플랫폼 계정 ID.
    :return: 발행된 글 수.
    """
    logger.info(f"Registering platform {platform_name} for user {user_id} (account: {account_id})")

    if platform_name == "tistory":
        posts = _collect_tistory(account_id)
    else:
        posts = _collect_rss(platform_name, account_id)

    if not posts:
        logger.info(f"No posts found for {platform_name}/{account_id}")
        return 0

    messages = []
    for post in posts:
        published_at = post.get("published_at")
        messages.append(
            {
                "user_id": user_id,
                "platform": platform_name,
                "article": {
                    "link": post["url"],
                    "published_at": (
                        published_at.isoformat()
                        if isinstance(published_at, datetime)
                        else published_at
                    ),
                    "title": "",
                },
            },
        )
    publish_messages(queue_name="new_posts", messages=messages)

    latest_published_at = max(
        (p["published_at"] for p in posts if p.get("published_at") is not None),
        default=None,
    )
    if latest_published_at is not None:
        platform_service.update_last_upload(
            user_id=user_id,
            platform_name=platform_name,
            last_upload_time=latest_published_at,
        )

    logger.info(f"Registered {len(posts)} posts for {platform_name}/{account_id}")
    return len(posts)
