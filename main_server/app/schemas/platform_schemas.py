from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class Platforms(str, Enum):
    """
        플랫폼 목록을 enum으로 관리합니다.
    """
    TISTORY="tistory"
    NAVER="naver"
    VELOG="velog"

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