from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.schemas.trend_schemas import GetTrendingKeywordsResponse
from app.services import trend_service
from app.core.verify_jwt import get_current_user_id

router = APIRouter(
    prefix="/api/trend",
    tags=["Trend"]
)

@router.get("/keywords", response_model=GetTrendingKeywordsResponse, status_code=status.HTTP_200_OK)
def get_trending_keywords_router(
    db: Session = Depends(get_db),
    field: str|None = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    인기 급상승 키워드를 반환하는 엔드포인트
    
    :param db: 데이터베이스 세션
    :type db: Session
    :param field: 키워드의 분야 (예: "It", "Bio", "Electronics"). 필수.
    :type field: str | None
    """
    if field is None:
        raise HTTPException(status_code=400, detail="field query parameter is required")
    
    # field가 존재하는지 검증
    field_obj = trend_service.get_field_matching(db, field)
    if not field_obj:
        raise HTTPException(status_code=400, detail="Invalid field")

    # 트렌드 키워드 가져오기
    res = trend_service.get_trending_keywords(db, field_obj)

    return res

