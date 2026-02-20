from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
import logging
from app.dependencies.database import get_db
from main_server.app.schemas.trend_schemas import GetTrendingKeywordsResponse

router = APIRouter(
    prefix="/api/trend",
    tags=["Trend"]
)

@router.get("/keywords", response_model=GetTrendingKeywordsResponse, status_code=status.HTTP_200_OK)
def get_trending_keywords(
    db: Session = Depends(get_db),
    field: str|None = None,
):
    """
    인기 급상승 키워드를 반환하는 엔드포인트
    
    :param db: 데이터베이스 세션
    :type db: Session
    :param field: 키워드의 분야 (예: "It", "Bio", "Electreonics"). 필수.
    :type field: str | None
    """
    if field is None:
        raise HTTPException(status_code=400, detail="field query parameter is required")
    
    res = get_trending_keywords(db, field)

    return res

