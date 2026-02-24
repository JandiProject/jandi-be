from app.schemas.trend_schemas import ArticleMentioningKeyword, GetArticlesMentioningKeywordResponse, GetTrendingKeywordsResponse, KeywordData
from sqlalchemy.orm import Session
from app.models.user_models import Fields
from app.models.trend_models import TrendingKeywordView, ArticlesMentioningKeywordsView
from collections import defaultdict
import base64

def get_trending_keywords(db: Session, field: Fields) -> GetTrendingKeywordsResponse:
    try:
        trending_keywords = db.query(TrendingKeywordView).filter(TrendingKeywordView.field_id == field.field_id).order_by(TrendingKeywordView.count.desc()).limit(10).all()
        result = GetTrendingKeywordsResponse(data=[KeywordData(keyword=str(kw.keyword), frequency= kw.count) for kw in trending_keywords]) # pyright: ignore[reportArgumentType]
        return result
    except Exception as e:
        raise e

def get_field_matching(db: Session, field: str) -> Fields:
    fields = db.query(Fields).filter(Fields.field_name == field).one_or_none()
    return fields

def get_articles_mentioning_keyword(db: Session,field: Fields) -> list[GetArticlesMentioningKeywordResponse]:
    try:
        articles = db.query(ArticlesMentioningKeywordsView).filter(ArticlesMentioningKeywordsView.field_id == field.field_id).all()
        result = []
        mapping = defaultdict(list)
        for article in articles:
            mapping[article.keyword].append(ArticleMentioningKeyword(
                id=article.id, # type: ignore
                title=article.title, # type: ignore
                url=article.url, # type: ignore
                source= base64.b64decode(article.source).decode() if article.source else None, # type: ignore
                summary=article.summary, # type: ignore
                published_at=article.published_at.isoformat()
            ))
        for keyword, articles in mapping.items():
            result.append(GetArticlesMentioningKeywordResponse(keyword=keyword, articles=articles)) # pyright: ignore[reportArgumentType]
        return result
    except Exception as e:
        raise e