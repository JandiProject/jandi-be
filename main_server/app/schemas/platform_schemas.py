from typing import List, Optional
from pydantic import BaseModel


class UserPlatformRequest(BaseModel):
    """ 유저-플랫폼 매핑 정보 요청 스키마 """
    platform_name: str
    account_id: str


class UserPlatformResponse(BaseModel):
    """ 유저-플랫폼 매핑 정보 응답 스키마 """
    status: str
    message: str
    platform: str
    registered_id: str

class ArticleSchema(BaseModel):
    """ RSS 피드에서 파싱한 글 정보 """
    title: str
    link: str
    published_at: str
    thumbnail: Optional[str] = None
    tags: Optional[List[str]] = None

class TistoryTokenResponse(BaseModel):
    """ 티스토리 인증 토큰 응답 스키마 """
    header: str


class NaverTokenResponse(BaseModel):
    verification_token: Optional[str] = None
    message: str


class VerificationResponse(BaseModel):
    """ 플랫폼 인증 결과 응답 스키마 """
    is_verified: bool   