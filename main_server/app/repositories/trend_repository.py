from sqlalchemy import Column
from sqlalchemy.orm import Session
from app.models.user_models import Fields
from app.models.trend_models import TrendingKeywordView, ArticlesMentioningKeywordsView, UsersMentioningKeywordsView


class TrendRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_field_by_name(self, field_name: str) -> Fields | None:
        """field 이름으로 sqlalchemy Field 객체를 반환함

        Args:
            field_name (str): 필드 이름

        Returns:
            Fields | None: 필드가 존재하면 필드 객체를, 존재하지 않으면 None 반환
        """
        return self.db.query(Fields).filter(Fields.field_name == field_name).one_or_none()

    def get_trending_keywords_by_field_id(self, field_id: Column | int) -> list[TrendingKeywordView]:
        """트렌딩 키워드 조회

        Args:
            field_id (Column | int): 필드 ID

        Returns:
            list[TrendingKeywordView]: 필드에 해당하는 트렌딩 키워드 목록
        """
        return (
            self.db.query(TrendingKeywordView)
            .filter(TrendingKeywordView.field_id == field_id)
            .order_by(TrendingKeywordView.count.desc())
            .limit(10)
            .all()
        )

    def get_articles_mentioning_keywords_by_field_id(self, field_id: Column | int) -> list[ArticlesMentioningKeywordsView]:
        """필드에 해당하는 트렌드 키워드를 언급하는 기사 조회

        Args:
            field_id (Column | int): 필드 id

        Returns:
            list[ArticlesMentioningKeywordsView]: 필드에 해당하는 트렌드 키워드를 언급하는 기사 목록
        """
        return (
            self.db.query(ArticlesMentioningKeywordsView)
            .filter(ArticlesMentioningKeywordsView.field_id == field_id)
            .all()
        )

    def get_top_users_mentioning_keywords(self, limit: int = 3, field_id: int = 1) -> list[UsersMentioningKeywordsView]:
        """트렌드 키워드를 많이 언급한 유저 (id, name) 목록 출력

        Args:
            limit (int, optional): 조회할 상위 유저 수. Defaults to 3.
            field_id (int, optional): 필드 ID. Defaults to 1.

        Returns:
            list[UsersMentioningKeywordsView]: 트렌드 키워드를 많이 언급한 유저 목록
        """
        return (
            self.db.query(UsersMentioningKeywordsView)
            .filter(UsersMentioningKeywordsView.field_id == field_id)
            .order_by(UsersMentioningKeywordsView.count.desc())
            .limit(limit)
            .all()
        )
