import logging
import os

import httpx

logger = logging.getLogger(__name__)

CRAWLER_SERVICE_URL = os.getenv(
    "CRAWLER_SERVICE_URL", "http://crawler-service-clusterip/verify"
)


class TistoryCrawlerParser:
    @staticmethod
    async def verify_header(account_id: str, expected_token: str) -> bool:
        """
        클러스터 내부 크롤링 서버에 티스토리 헤더 검증을 요청한다.
        연결 실패 시 httpx.RequestError를 그대로 전파한다.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CRAWLER_SERVICE_URL,
                json={
                    "platform_name": "tistory",
                    "account_id": account_id,
                    "target_token": expected_token,
                },
                timeout=60.0,
            )

        if response.status_code != 200:
            logger.warning(
                "크롤러 비정상 응답: %s %s", response.status_code, response.text
            )
            return False

        try:
            return bool(response.json().get("is_verified", False))
        except Exception:
            return False
