from schemas.trend_schemas import GetTrendingKeywordsResponse
from sqlalchemy.orm import Session

def get_trending_keywords(db: Session, field: str) -> GetTrendingKeywordsResponse:
    #return GetTrendingKeywordsResponse()
