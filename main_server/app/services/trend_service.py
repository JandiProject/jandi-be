from app.schemas.trend_schemas import ArticleMentioningKeyword, GetArticlesMentioningKeywordResponse, GetTrendingKeywordsResponse, KeywordData
from sqlalchemy.orm import Session
from app.models.user_models import Fields
from app.repositories.trend_repository import TrendRepository
from collections import defaultdict
import base64

def get_trending_keywords(db: Session, field: Fields) -> GetTrendingKeywordsResponse:
    """트렌드 키워드 반환

    Args:
        db (Session): db 세션
        field (Fields): 분야

    Raises:
        e: 

    Returns:
        GetTrendingKeywordsResponse: 트렌드 키워드 반환
    """
    trend_repository = TrendRepository(db)
    trending_keywords = trend_repository.get_trending_keywords_by_field_id(field.field_id)
    result = GetTrendingKeywordsResponse(data=[KeywordData(keyword=str(kw.keyword), frequency= kw.count) for kw in trending_keywords]) # pyright: ignore[reportArgumentType]
    return result


def get_field_matching(db: Session, field: str) -> Fields| None:
    """ field 이름에 맞는 Field 객체 반환

    Args:
        db (Session): db 세션
        field (str): 필드 이름

    Returns:
        Fields | None: field가 존재하면 Fields 객체를, 존재하지 않으면 None 반환
    """
    trend_repository = TrendRepository(db)
    fields = trend_repository.get_field_by_name(field)
    return fields

def get_articles_mentioning_keyword(db: Session,field: Fields) -> list[GetArticlesMentioningKeywordResponse]:
    """해당 분야의 키워드를 언급한 기사 반환

    Args:
        db (Session): db 세션
        field (Fields): 분야

    Raises:
        e: 

    Returns:
        list[GetArticlesMentioningKeywordResponse]: 해당 분야의 키워드를 언급한 기사 목록
    """

    trend_repository = TrendRepository(db)
    articles = trend_repository.get_articles_mentioning_keywords_by_field_id(field.field_id)
    result = []
    mapping = defaultdict(list)
    
    for article in articles:
        try:
            source = base64.b64decode(article.source).decode() if article.source else "" # pyright: ignore
        except Exception:
            source = ""

        mapping[article.keyword].append(ArticleMentioningKeyword(
            id=article.id, # type: ignore
            title=article.title, # type: ignore
            url=article.url, # type: ignore
            source=source, # type: ignore
            summary=article.summary, # type: ignore
            published_at=article.published_at.isoformat()
        ))
    for keyword, article_list in mapping.items():
        result.append(GetArticlesMentioningKeywordResponse(keyword=keyword, articles=article_list)) # pyright: ignore[reportArgumentType]
    return result
    
def get_users_mentioning_keyword(db: Session, field_id: int) -> list[tuple[str, str]]:
    """트렌딩 키워드를 많이 언급한 유저 (id, name) 목록 출력

    Args:
        db (Session): db 세션

    Raises:
        e: 

    Returns:
        list[tuple[str, str]]: 유저의 id, name 튜플 리스트
    """

    trend_repository = TrendRepository(db)
    users = trend_repository.get_top_users_mentioning_keywords(limit=3, field_id=field_id)
    names = []
    for user in users:
        names.append((user.user_id, user.name))
    names = list(dict.fromkeys(names)) # type: ignore
    return list(names)

 