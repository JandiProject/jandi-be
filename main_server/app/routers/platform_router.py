from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging
from app.dependencies.database import get_db
from app.dependencies.post_observer import notify_platform_registered
from app.schemas.platform_schemas import ArticleSchema, UserPlatformRequest, UserPlatformResponse
from app.core.verify_jwt import get_current_user_id
from app.services import platform_service
from app.models.platform_models import Platform

router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"]
)

logger = logging.getLogger(__name__)


@router.put("", status_code=status.HTTP_200_OK, response_model=UserPlatformResponse)
def register_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> UserPlatformResponse:
    """
    유저-플랫폼 매핑을 등록 또는 업데이트하고, post_observer에 글 수집을 요청합니다.

    :param req: 플랫폼 이름 및 계정 ID.
    :param db: DB 세션.
    :param user_id: JWT에서 추출한 유저 ID.
    :return: 등록 결과 응답.
    """
    # 플랫폼 정보 조회
    platform_info: Platform = platform_service.get_platform_info(db, req.platform_name)

    # 유저-플랫폼 매핑 추가 또는 업데이트
    platform_service.add_user_platform_mapping(db, user_id, platform_info.platform_id, req.account_id)

    # post_observer에 글 수집 요청
    notify_platform_registered(
        user_id=user_id,
        platform_name=req.platform_name,
        account_id=req.account_id,
    )

    return UserPlatformResponse(
        status="ok",
        message="플랫폼이 등록되었습니다.",
        platform=req.platform_name,
        registered_id=req.account_id,
    )


@router.delete("", status_code=status.HTTP_200_OK)
def delete_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    유저-플랫폼 매핑을 삭제합니다.

    :param req: 플랫폼 이름 및 계정 ID.
    :param db: DB 세션.
    :param user_id: JWT에서 추출한 유저 ID.
    :return: 삭제 완료 메시지.
    """
    platform_info: Platform = platform_service.get_platform_info(db, req.platform_name)

    platform_service.delete_user_platform_mapping(db, user_id, platform_info.platform_id, req.platform_name)

    return {"message": "삭제 완료"}


@router.get("", status_code=status.HTTP_200_OK)
def get_platforms(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[dict]:
    """
    유저에 등록된 플랫폼 목록을 조회합니다.

    :param db: DB 세션.
    :param user_id: JWT에서 추출한 유저 ID.
    :return: 등록된 플랫폼 목록.
    """
    res: list[dict] = platform_service.get_user_platforms(db, user_id)
    return res