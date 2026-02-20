from typing import List, Optional
from pydantic import BaseModel


class UserPlatformRequest(BaseModel):
    platform_name: str
    account_id: str


class UserPlatformResponse(BaseModel):
    status: str
    message: str
    platform: str
    registered_id: str

class ArticleSchema(BaseModel):
    # RSS 피드에서 파싱한 글 정보
    title: str
    link: str
    published_at: str
    thumbnail: Optional[str] = None
    tags: Optional[List[str]] = None