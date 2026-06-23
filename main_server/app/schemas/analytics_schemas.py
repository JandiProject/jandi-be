from datetime import date

from pydantic import BaseModel, Field


class _UserCategoryCount(BaseModel):
    """유저 통계 카테고리-카운트 페어."""

    category: str
    count: int = Field(ge=0)


class UserStatResponse(BaseModel):
    """기존 유저 통계 응답 모델."""

    duration: int = Field(ge=0)
    category: list[_UserCategoryCount]
    count: int = Field(ge=0)
    created_at: date


class LevelInfo(BaseModel):
    """사용자 레벨 정보."""

    current_level: int = Field(ge=0)
    level_name: str | None
    level_message: str | None


class RankingInfo(BaseModel):
    """사용자 랭킹 정보."""

    rank: int = Field(ge=0)
    total_user: int = Field(ge=0)


class AnalyticsSummaryResponse(BaseModel):
    """요약 통계 응답 모델."""

    total_posts: int = Field(ge=0)
    active_months: int = Field(ge=0)
    active_days: int = Field(ge=0)
    first_post_date: date | None
    latest_post_date: date | None
    primary_field: str | None
    level_info: LevelInfo
    ranking: RankingInfo


class TopicRatioItem(BaseModel):
    """카테고리 비율 아이템."""

    category: str
    count: int = Field(ge=0)
    percentage: float = Field(ge=0, le=100)


class AnalyticsCategoryRatioResponse(BaseModel):
    """개인 카테고리 비율 응답 모델."""

    total_posts: int = Field(ge=0)
    topic_ratios: list[TopicRatioItem]


class GlobalCategoryRatioResponse(BaseModel):
    """전체 카테고리 비율 응답 모델."""

    total_posts: int = Field(ge=0)
    global_topic_ratios: list[TopicRatioItem]


class KeywordRankingItem(BaseModel):
    """키워드 랭킹 아이템."""

    rank: int = Field(ge=1)
    keyword: str
    frequency: int = Field(ge=0)


class AnalyticsKeywordRankingResponse(BaseModel):
    """키워드 랭킹 응답 모델."""

    total_posts: int = Field(ge=0)
    keyword_rankings: list[KeywordRankingItem]
