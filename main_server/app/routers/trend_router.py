from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.schemas.trend_schemas import GetArticlesMentioningKeywordResponse, GetTrendingKeywordsResponse
from app.services import trend_service

router = APIRouter(
    prefix="/api/trend",
    tags=["Trend"]
)

@router.get("/keywords", response_model=GetTrendingKeywordsResponse, status_code=status.HTTP_200_OK)
def get_trending_keywords_router(
    db: Session = Depends(get_db),
    field: str|None = None,
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

@router.get("/articles", status_code=status.HTTP_200_OK, response_model=list[GetArticlesMentioningKeywordResponse])
def get_articles_mentioning_keyword_router(
    db: Session = Depends(get_db),
    field: str|None = None,
):
    """
    특정 분야에서 언급된 기사들을 반환하는 엔드포인트
    
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

    # 언급된 기사들 가져오기
    res = trend_service.get_articles_mentioning_keyword(db, field_obj)

    return res