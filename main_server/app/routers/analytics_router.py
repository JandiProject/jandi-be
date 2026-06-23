from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.verify_jwt import get_current_user_id
from app.dependencies.database import get_db
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics_schemas import (
    AnalyticsCategoryRatioResponse,
    AnalyticsKeywordRankingResponse,
    AnalyticsSummaryResponse,
    GlobalCategoryRatioResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """
    AnalyticsService 의존성을 생성합니다.

    :param db: DB 세션.
    :return: AnalyticsService 인스턴스.
    """
    repository = AnalyticsRepository(db)
    return AnalyticsService(repository)


@router.get("/summary", response_model=AnalyticsSummaryResponse, status_code=status.HTTP_200_OK)
def get_analytics_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    user_id: str = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    """
    유저 요약 통계를 조회합니다.

    :param start_date: 조회 시작 날짜.
    :param end_date: 조회 종료 날짜.
    :param user_id: 인증 유저 ID.
    :param service: Analytics 서비스.
    :return: 유저 요약 통계.
    """
    return service.get_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/category-ratios",
    response_model=AnalyticsCategoryRatioResponse,
    status_code=status.HTTP_200_OK,
)
def get_analytics_category_ratios(
    start_date: date = Query(...),
    end_date: date = Query(...),
    field: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCategoryRatioResponse:
    """
    유저 카테고리 비율을 조회합니다.

    :param start_date: 조회 시작 날짜.
    :param end_date: 조회 종료 날짜.
    :param field: 필드 코드 또는 이름.
    :param user_id: 인증 유저 ID.
    :param service: Analytics 서비스.
    :return: 유저 카테고리 비율.
    """
    return service.get_category_ratios(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        field=field,
    )


@router.get(
    "/keyword-rankings",
    response_model=AnalyticsKeywordRankingResponse,
    status_code=status.HTTP_200_OK,
)
def get_analytics_keyword_rankings(
    start_date: date = Query(...),
    end_date: date = Query(...),
    field: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsKeywordRankingResponse:
    """
    유저 키워드 랭킹을 조회합니다.

    :param start_date: 조회 시작 날짜.
    :param end_date: 조회 종료 날짜.
    :param field: 필드 코드 또는 이름.
    :param user_id: 인증 유저 ID.
    :param service: Analytics 서비스.
    :return: 유저 키워드 랭킹.
    """
    return service.get_keyword_rankings(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        field=field,
    )


@router.get(
    "/global/category-ratios",
    response_model=GlobalCategoryRatioResponse,
    status_code=status.HTTP_200_OK,
)
def get_global_analytics_category_ratios(
    start_date: date = Query(...),
    end_date: date = Query(...),
    field: str = Query(...),
    service: AnalyticsService = Depends(get_analytics_service),
) -> GlobalCategoryRatioResponse:
    """
    전체 유저 카테고리 비율을 조회합니다.

    :param start_date: 조회 시작 날짜.
    :param end_date: 조회 종료 날짜.
    :param field: 필드 코드 또는 이름.
    :param service: Analytics 서비스.
    :return: 전체 유저 카테고리 비율.
    """
    return service.get_global_category_ratios(
        start_date=start_date,
        end_date=end_date,
        field=field,
    )


@router.get(
    "/global/keyword-rankings",
    response_model=AnalyticsKeywordRankingResponse,
    status_code=status.HTTP_200_OK,
)
def get_global_analytics_keyword_rankings(
    start_date: date = Query(...),
    end_date: date = Query(...),
    field: str = Query(...),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsKeywordRankingResponse:
    """
    전체 유저 키워드 랭킹을 조회합니다.

    :param start_date: 조회 시작 날짜.
    :param end_date: 조회 종료 날짜.
    :param field: 필드 코드 또는 이름.
    :param service: Analytics 서비스.
    :return: 전체 유저 키워드 랭킹.
    """
    return service.get_global_keyword_rankings(
        start_date=start_date,
        end_date=end_date,
        field=field,
    )
