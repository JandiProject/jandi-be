from pydantic import BaseModel


class TrendBaseSchema(BaseModel):
    pass

class KeywordData(BaseModel):
    keyword: str
    values: list[int]

class GetTrendingKeywordsResponse(BaseModel):
    timeline: list[str]
    data: list[KeywordData]