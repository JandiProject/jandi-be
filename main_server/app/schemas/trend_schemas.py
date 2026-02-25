from pydantic import BaseModel

from app.schemas.jandi_schemas import GetJandiResponse


class TrendBaseSchema(BaseModel):
    pass

class KeywordData(BaseModel):
    keyword: str
    frequency: int

class GetTrendingKeywordsResponse(BaseModel):
    data: list[KeywordData]

class ArticleMentioningKeyword(BaseModel):
    id: str
    title: str
    url: str
    source: str
    summary: str | None
    published_at: str

class GetArticlesMentioningKeywordResponse(BaseModel):
    keyword: str
    articles: list[ArticleMentioningKeyword]

class GetUsersMentioningKeywordResponse(BaseModel):
    name: str
    jandi_data: list[GetJandiResponse]