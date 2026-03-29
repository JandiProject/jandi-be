import logging

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.verify_jwt import get_current_user_id
from app.dependencies.database import get_db
from app.schemas.platform_schemas import (
    NaverTokenResponse,
    TistoryTokenResponse,
    UserPlatformRequest,
    VerificationResponse,
)
from app.models.platform_models import Platform
from app.parsers.tistory_crawler import TistoryCrawlerParser
from app.repositories.platform_repository import PlatformRepository
from app.services import platform_service

router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"],
)

logger = logging.getLogger(__name__)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    platform_info: Platform = platform_service.get_platform_info(db, req.platform_name)
    platform_service.delete_user_platform_mapping(
        db, user_id, platform_info.platform_id, req.platform_name
    )


@router.get("")
def get_platforms(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return platform_service.get_user_platforms(db, user_id)


@router.get("/token/naver", response_model=NaverTokenResponse)
async def get_naver_verification_token(
    account_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    token, message = await platform_service.issue_naver_verification_token(db, user_id, account_id)
    return NaverTokenResponse(verification_token=token, message=message)


@router.get("/token/tistory", response_model=TistoryTokenResponse)
def get_tistory_verification_token(
    account_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    token = platform_service.get_tistory_token_logic(db, user_id, account_id)
    return TistoryTokenResponse(header=token)


@router.get("/verification/naver", response_class=HTMLResponse)
def verify_naver_platform(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ok, html, uid, aid = platform_service.complete_naver_verification_by_token(db, token)
    if ok and uid and aid:
        background_tasks.add_task(
            platform_service.trigger_platform_added_event, uid, "naver", aid
        )
    return HTMLResponse(content=html)


@router.get("/verification/tistory", response_model=VerificationResponse)
async def verify_tistory_platform(
    account_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    platform_info = platform_service.get_platform_info(db, "tistory")
    saved_token = platform_service.get_user_verification_token(db, user_id, "tistory")

    if not saved_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="발급된 인증 토큰이 없습니다. 먼저 인증 헤더를 발급받아 주세요.",
        )

    repo = PlatformRepository(db)
    verification = repo.get_verification_token(user_id, platform_info.platform_id)
    if (
        not verification
        or not verification.pending_account_id
        or verification.pending_account_id != account_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="요청한 계정이 발급 시 입력한 블로그 ID와 일치하지 않습니다.",
        )

    try:
        is_verified = await TistoryCrawlerParser.verify_header(account_id, saved_token)
    except httpx.RequestError as exc:
        logger.exception("티스토리 크롤러 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"크롤링 서비스에 연결할 수 없습니다: {exc}",
        )

    if not is_verified:
        return VerificationResponse(is_verified=False)

    platform_service.update_verification_status(db, user_id, "tistory", account_id)
    background_tasks.add_task(
        platform_service.trigger_platform_added_event, user_id, "tistory", account_id
    )

    return VerificationResponse(is_verified=True)
