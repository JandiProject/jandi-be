import os
import logging
import httpx

logger = logging.getLogger(__name__)

POST_OBSERVER_URL = os.getenv("POST_OBSERVER_URL", "http://localhost:8001")


def notify_platform_registered(user_id: str, platform_name: str, account_id: str) -> None:
    """
    post_observer 서버에 플랫폼 등록 이벤트를 전달합니다.

    :param user_id: 유저 ID.
    :param platform_name: 플랫폼 이름.
    :param account_id: 플랫폼 계정 ID.
    :return: None.
    """
    try:
        response = httpx.post(
            f"{POST_OBSERVER_URL}/api/observer/register-platform",
            json={
                "user_id": user_id,
                "platform_name": platform_name,
                "account_id": account_id,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info(f"Notified post_observer: {platform_name}/{account_id} for user {user_id}")
    except Exception as e:
        # 수집 실패가 플랫폼 등록 자체를 막으면 안 되므로 로그만 남김
        logger.error(f"Failed to notify post_observer: {e}")
