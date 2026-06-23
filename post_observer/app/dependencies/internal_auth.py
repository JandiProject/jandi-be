from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def require_internal_token(
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> None:
    """
    내부 서버 간 호출에 사용되는 정적 토큰을 검증합니다.

    POST_OBSERVER_INTERNAL_TOKEN 환경변수가 설정되지 않은 경우(로컬 개발 환경 등)
    인증을 건너뜁니다. 설정된 경우 토큰이 일치해야 합니다.

    :param x_internal_token: 요청 헤더의 내부 토큰.
    :return: None.
    """
    configured_token = os.getenv("POST_OBSERVER_INTERNAL_TOKEN")
    if not configured_token:
        # 토큰 미설정 시 로컬 개발 환경으로 간주하고 통과
        return

    if x_internal_token is None or not secrets.compare_digest(x_internal_token, configured_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
