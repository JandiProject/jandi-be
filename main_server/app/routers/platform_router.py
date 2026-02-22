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

@router.get("/token")
def get_verification_token(
    platform_name: str, # 쿼리 파라미터: naver, tistory, velog
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """17번 명세: 플랫폼 검증용 토큰 발급. 플랫폼에 따라 다르게 진행하기"""
    token_data = platform_service.get_or_create_token(db, user_id, platform_name)
    
    return {
        "verification_token": token_data.token,
        "message": "발급된 토큰을 해당 플랫폼의 소개글이나 게시글에 포함시킨 후 검증을 진행해주세요."
    }

@router.put("/verification", status_code=status.HTTP_200_OK)
def verify_platform(
    req: UserPlatformRequest, # body: { platform_name, account_id }
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """18번 명세: 메인 서버에서 직접 플랫폼 검증 수행"""
    
    # 1. DB에서 이 사용자가 발급받았던 토큰 정보 조회
    # (앞서 /token API에서 생성했던 값을 가져옵니다)
    saved_token = platform_service.get_user_verification_token(db, user_id, req.platform_name)
    
    if not saved_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="발급된 검증 토큰이 없습니다. 먼저 토큰을 발급받으세요."
        )

    # 2. 메인 서버에서 직접 해당 플랫폼 페이지 크롤링/조회 수행
    # (예: 네이버 블로그 소개글이나 벨로그 프로필에서 saved_token이 있는지 확인)
    is_verified = platform_service.direct_verify_on_platform(
        platform_name=req.platform_name,
        account_id=req.account_id,
        target_token=saved_token
    )

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="검증 실패: 해당 플랫폼에서 토큰을 찾을 수 없습니다."
        )

    # 3. 검증 성공 시 매핑 테이블 상태 업데이트 (예: is_verified = True)
    platform_service.update_verification_status(db, user_id, req.platform_name, req.account_id)

    return {"message": f"{req.platform_name} 인증이 완료되었습니다."}