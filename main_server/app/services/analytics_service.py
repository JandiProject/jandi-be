from __future__ import annotations

from datetime import date, datetime, time

from fastapi import HTTPException, status

from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics_schemas import (
    AnalyticsCategoryRatioResponse,
    AnalyticsKeywordRankingResponse,
    AnalyticsSummaryResponse,
    GlobalCategoryRatioResponse,
    KeywordRankingItem,
    LevelInfo,
    RankingInfo,
    TopicRatioItem,
)


class AnalyticsService:
    """Analytics 비즈니스 로직을 담당하는 service."""

    def __init__(self, repository: AnalyticsRepository):
        """
        AnalyticsService 생성자.

        :param repository: Analytics 전용 repository.
        :return: None.
        """
        self.repository = repository

    def _resolve_datetime_range(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[datetime, datetime]:
        """
        쿼리 파라미터 날짜를 datetime 범위로 변환합니다.

        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :return: (시작 datetime, 종료 datetime).
        """
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date",
            )
        return (
            datetime.combine(start_date, time.min),
            datetime.combine(end_date, time.max),
        )

    def _resolve_field_id(self, field: str) -> int:
        """
        field 이름으로 DB에서 field_id를 조회합니다.

        :param field: DB FIELDS 테이블의 field_name.
        :return: field_id.
        :raises HTTPException: field가 비어있거나 DB에 존재하지 않으면 400.
        """
        normalized = field.strip().lower()
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="field must not be empty",
            )

        field_id = self.repository.get_field_id_by_name(normalized)
        if field_id is not None:
            return field_id

        supported = self.repository.get_all_field_names()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field '{field}'. Supported values: {', '.join(supported)}",
        )

    def _display_field_name(self, field_id: int | None) -> str | None:
        """
        field_id를 DB에서 조회해 표시명(대문자)으로 변환합니다.

        :param field_id: 필드 ID.
        :return: 표시용 필드명 또는 None.
        """
        if field_id is None:
            return None
        field_name = self.repository.get_field_name_by_id(field_id)
        if field_name is None:
            return None
        return str(field_name).upper()

    def get_summary(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> AnalyticsSummaryResponse:
        """
        유저 통계 요약을 조회합니다.

        :param user_id: 유저 ID.
        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :return: 요약 통계 응답.
        """
        start_datetime, end_datetime = self._resolve_datetime_range(start_date, end_date)

        total_posts = self.repository.get_total_posts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=None,
            user_id=user_id,
        )
        active_days = self.repository.get_user_active_days(
            user_id=user_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        active_months = self.repository.get_user_active_months(
            user_id=user_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        first_post_date, latest_post_date = self.repository.get_user_first_and_latest_post_dates(
            user_id=user_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        primary_field_id = self.repository.get_user_primary_field_id(
            user_id=user_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        current_level, level_name, level_message = self.repository.get_level_info_by_post_count(
            total_posts=total_posts
        )
        rank, total_user = self.repository.get_user_ranking(
            user_id=user_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        return AnalyticsSummaryResponse(
            total_posts=total_posts,
            active_months=active_months,
            active_days=active_days,
            first_post_date=first_post_date,
            latest_post_date=latest_post_date,
            primary_field=self._display_field_name(primary_field_id),
            level_info=LevelInfo(
                current_level=current_level,
                level_name=level_name,
                level_message=level_message,
            ),
            ranking=RankingInfo(rank=rank, total_user=total_user),
        )

    def _build_topic_ratio_items(
        self,
        category_counts: list[tuple[str, int]],
    ) -> tuple[int, list[TopicRatioItem]]:
        """
        카테고리 카운트를 TopicRatioItem 목록으로 변환합니다.

        :param category_counts: (카테고리, 개수) 목록.
        :return: (총 게시글 수, TopicRatioItem 목록).
        """
        total_posts = sum(count for _, count in category_counts)
        items = [
            TopicRatioItem(
                category=category,
                count=count,
                percentage=round((count / total_posts) * 100, 2) if total_posts else 0.0,
            )
            for category, count in category_counts
        ]
        return total_posts, items

    def get_category_ratios(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        field: str,
    ) -> AnalyticsCategoryRatioResponse:
        """
        유저 기준 카테고리 비율을 조회합니다.

        :param user_id: 유저 ID.
        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :param field: 필드 코드.
        :return: 카테고리 비율 응답.
        """
        start_datetime, end_datetime = self._resolve_datetime_range(start_date, end_date)
        field_id = self._resolve_field_id(field)
        category_counts = self.repository.get_category_counts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
            user_id=user_id,
        )
        total_posts, items = self._build_topic_ratio_items(category_counts)
        return AnalyticsCategoryRatioResponse(
            total_posts=total_posts,
            topic_ratios=items,
        )

    def _build_keyword_ranking_response(
        self,
        keyword_counts: list[tuple[str, int]],
        total_posts: int,
    ) -> AnalyticsKeywordRankingResponse:
        """
        키워드 카운트를 명세 응답 형태로 변환합니다.

        :param keyword_counts: (키워드, 개수) 목록.
        :param total_posts: 총 게시글 수.
        :return: 키워드 랭킹 응답.
        """
        keyword_rankings = [
            KeywordRankingItem(rank=index, keyword=keyword, frequency=count)
            for index, (keyword, count) in enumerate(keyword_counts, start=1)
        ]
        return AnalyticsKeywordRankingResponse(
            total_posts=total_posts,
            keyword_rankings=keyword_rankings,
        )

    def get_keyword_rankings(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        field: str,
    ) -> AnalyticsKeywordRankingResponse:
        """
        유저 기준 키워드 랭킹을 조회합니다.

        :param user_id: 유저 ID.
        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :param field: 필드 코드.
        :return: 키워드 랭킹 응답.
        """
        start_datetime, end_datetime = self._resolve_datetime_range(start_date, end_date)
        field_id = self._resolve_field_id(field)
        keyword_counts = self.repository.get_keyword_counts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
            user_id=user_id,
        )
        total_posts = self.repository.get_total_posts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
            user_id=user_id,
        )
        return self._build_keyword_ranking_response(
            keyword_counts=keyword_counts,
            total_posts=total_posts,
        )

    def get_global_category_ratios(
        self,
        start_date: date,
        end_date: date,
        field: str,
    ) -> GlobalCategoryRatioResponse:
        """
        전체 유저 기준 카테고리 비율을 조회합니다.

        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :param field: 필드 코드.
        :return: 카테고리 비율 응답.
        """
        start_datetime, end_datetime = self._resolve_datetime_range(start_date, end_date)
        field_id = self._resolve_field_id(field)
        category_counts = self.repository.get_category_counts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
        )
        total_posts, items = self._build_topic_ratio_items(category_counts)
        return GlobalCategoryRatioResponse(
            total_posts=total_posts,
            global_topic_ratios=items,
        )

    def get_global_keyword_rankings(
        self,
        start_date: date,
        end_date: date,
        field: str,
    ) -> AnalyticsKeywordRankingResponse:
        """
        전체 유저 기준 키워드 랭킹을 조회합니다.

        :param start_date: 시작 날짜.
        :param end_date: 종료 날짜.
        :param field: 필드 코드.
        :return: 키워드 랭킹 응답.
        """
        start_datetime, end_datetime = self._resolve_datetime_range(start_date, end_date)
        field_id = self._resolve_field_id(field)
        keyword_counts = self.repository.get_keyword_counts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
        )
        total_posts = self.repository.get_total_posts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
        )
        return self._build_keyword_ranking_response(
            keyword_counts=keyword_counts,
            total_posts=total_posts,
        )
