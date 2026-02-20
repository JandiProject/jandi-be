from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from app.dependencies.database import get_db
from app.schemas.platform_schemas import UserPlatformRequest
from app.core.verify_jwt import get_current_user_id
from app.services import platform_service
from app.models.platform_models import Platform
router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"]
)

logger = logging.getLogger(__name__)


@router.put("", status_code=status.HTTP_200_OK)
def register_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):
    # 플랫폼 정보 조회
    platform_info: Platform = platform_service.get_platform_info(db, req.platform_name)

    # 유저-플랫폼 매핑 추가 또는 업데이트
    platform_service.add_user_platform_mapping(db, user_id, platform_info.platform_id, req.account_id)

    # 메시지큐에 넣을 데이터 생성 (궁극적으로 이 부분은 없어지는 게 나아보임)
    data = []
    platform_service.make_article_data(data, req.platform_name, req.account_id, user_id)

    # TODO: 게시글 데이터를 통째로 MQ로 보내는 것은 비효율적임. 플랫폼 정보만 발행하는 게 나아보임. 그러면 main server에서 rss 파싱을 안해도 됨
    # 우선 메시지큐 기능 복구될 때까지 주석처리
    # publish_message("platform_register", data)

    return

@router.delete("")
def delete_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):

    platform_info: Platform = platform_service.get_platform_info(db, req.platform_name)

    if not platform_info:
        raise HTTPException(status_code=404, detail=f"지원하지 않는 플랫폼: {req.platform_name}")
    
    platform_service.delete_user_platform_mapping(db, user_id, platform_info.platform_id, req.platform_name)

    return {
        "message": "삭제 완료"
    }

@router.get("")
def get_platforms(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):
    res: list[dict] = platform_service.get_user_platforms(db, user_id)
    return res