from pydantic import BaseModel


class TrendBaseSchema(BaseModel):
    pass

class KeywordData(BaseModel):
    keyword: str
    frequency: int

class GetTrendingKeywordsResponse(BaseModel):
    data: list[KeywordData]