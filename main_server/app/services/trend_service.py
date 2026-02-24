from schemas.trend_schemas import GetTrendingKeywordsResponse
from sqlalchemy.orm import Session
from app.models.user_models import Fields

def get_trending_keywords(db: Session, field: Fields) -> GetTrendingKeywordsResponse:
    #return GetTrendingKeywordsResponse()

def get_field_matching(db: Session, field: str) -> Fields:
    fields = db.query(Fields).filter(Fields.field_name == field).one_or_none()
    return fields