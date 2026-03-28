from app.services import rss_service, platform_service
from app.dependencies.rabbitmq import publish_message
import logging

logger = logging.getLogger(__name__)


def register_platform(user_id: str, platform_name: str, account_id: str) -> int:
    """
    플랫폼 등록 시 해당 유저의 기존 글을 RSS로 수집하고 RabbitMQ에 발행합니다.

    :param user_id: 유저 ID.
    :param platform_name: 플랫폼 이름 (naver, tistory, velog).
    :param account_id: 플랫폼 계정 ID.
    :return: 수집된 글 수.
    """
    logger.info(f"Registering platform {platform_name} for user {user_id} (account: {account_id})")

    articles = rss_service.fetch_rss(platform_name, account_id)

    if not articles:
        logger.info(f"No articles found for {platform_name}/{account_id}")
        return 0

    for article in articles:
        publish_message(
            queue_name="new_posts",
            message={
                "user_id": user_id,
                "platform": platform_name,
                "article": article.model_dump(mode="json"),
            },
        )

    platform_service.update_last_upload(
        user_id=user_id,
        platform_name=platform_name,
        last_upload_time=max(a.published_at for a in articles),
    )

    logger.info(f"Registered {len(articles)} articles for {platform_name}/{account_id}")
    return len(articles)
