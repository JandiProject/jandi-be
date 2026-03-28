from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── RSS ──────────────────────────────────────────────────────────────────────

class RssUrlsResponse(BaseModel):
    """RSS 파싱 결과 응답 모델."""

    platform: str
    account_id: str
    articles: list[dict]


# ── Crawl ─────────────────────────────────────────────────────────────────────

class CrawlContentsRequest(BaseModel):
    """본문 크롤링 요청 모델."""

    urls: list[str] = Field(min_length=1, description="크롤링할 URL 목록")


class CrawlResultItem(BaseModel):
    """단일 URL 크롤링 결과."""

    url: str
    content: str | None


class CrawlContentsResponse(BaseModel):
    """본문 크롤링 결과 응답 모델."""

    results: list[CrawlResultItem]


# ── Observer ──────────────────────────────────────────────────────────────────

class CheckNewPostsResponse(BaseModel):
    """새 글 수집 결과 응답 모델."""

    total_new_posts: int = Field(ge=0, description="수집된 새 글 수")


class CheckInactiveUsersResponse(BaseModel):
    """비활성 사용자 알림 결과 응답 모델."""

    total_reminders: int = Field(ge=0, description="발송된 알림 수")


class RegisterPlatformRequest(BaseModel):
    """플랫폼 등록 요청 모델."""

    user_id: str = Field(description="유저 ID")
    platform_name: Literal["naver", "tistory", "velog"] = Field(description="플랫폼 이름")
    account_id: str = Field(description="플랫폼 계정 ID")


class RegisterPlatformResponse(BaseModel):
    """플랫폼 등록 수집 결과 응답 모델."""

    message: str = Field(default="수집이 시작되었습니다.")
