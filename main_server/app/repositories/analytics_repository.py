from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session

from app.models.post_models import POST_KEYWORD, Posts
from app.models.trend_models import Keyword
from app.models.user_models import Fields, LevelThreshold, User


class AnalyticsRepository:
    """Analytics 전용 DB 조회를 담당하는 repository."""

    def __init__(self, db: Session):
        """
        AnalyticsRepository 생성자.

        :param db: SQLAlchemy DB 세션.
        :return: None.
        """
        self.db: Session = db

    def _apply_post_filters(
        self,
        query: Query[Any],
        start_datetime: datetime,
        end_datetime: datetime,
        field_id: int | None,
        user_id: str | None = None,
    ) -> Query[Any]:
        """
        POSTS 기준 공통 필터를 query에 적용합니다.

        :param query: 필터를 적용할 SQLAlchemy Query.
        :param start_datetime: 조회 시작 일시.
        :param end_datetime: 조회 종료 일시.
        :param field_id: 필드 ID(없으면 전체).
        :param user_id: 유저 ID(없으면 전체).
        :return: 필터 적용된 Query.
        """
        query = query.filter(Posts.date >= start_datetime, Posts.date <= end_datetime)
        if user_id is not None:
            query = query.filter(Posts.user_id == user_id)
        if field_id is not None:
            query = query.filter(Posts.field_id == field_id)
        return query

    def get_total_user_count(self) -> int:
        """
        전체 사용자 수를 조회합니다.

        :return: 전체 사용자 수.
        """
        total_user = self.db.query(func.count(User.user_id)).scalar()
        return int(total_user or 0)

    def get_field_id_by_name(self, field_name: str) -> int | None:
        """
        field 이름으로 field_id를 조회합니다.

        :param field_name: 필드 이름.
        :return: field_id 또는 None.
        """
        field: Fields | None = (
            self.db.query(Fields)
            .filter(func.lower(Fields.field_name) == field_name.lower())
            .one_or_none()
        )
        if field is None:
            return None
        return int(field.field_id)

    def get_field_name_by_id(self, field_id: int) -> str | None:
        """
        field_id로 field 이름을 조회합니다.

        :param field_id: 필드 ID.
        :return: 필드 이름 또는 None.
        """
        field: Fields | None = (
            self.db.query(Fields).filter(Fields.field_id == field_id).one_or_none()
        )
        if field is None:
            return None
        return str(field.field_name)

    def get_all_field_names(self) -> list[str]:
        """
        DB에 등록된 모든 field 이름 목록을 조회합니다.

        :return: field_name 목록 (소문자).
        """
        rows: list[Fields] = self.db.query(Fields).order_by(Fields.field_id.asc()).all()
        return [str(row.field_name).lower() for row in rows]

    def get_level_info_by_post_count(self, total_posts: int) -> tuple[int, str | None, str | None]:
        """
        게시글 수 기준 레벨 정보를 조회합니다.

        :param total_posts: 게시글 수.
        :return: (현재 레벨 번호, 레벨 이름, 레벨 메시지).
        """
        rows: list[LevelThreshold] = (
            self.db.query(LevelThreshold).order_by(LevelThreshold.min_post.asc()).all()
        )
        current_level = 0
        level_name: str | None = None
        level_message: str | None = None

        for index, row in enumerate(rows, start=1):
            if total_posts < int(row.min_post):
                break
            current_level = index
            level_name = str(row.level_name)
            level_message = str(row.message)

        return current_level, level_name, level_message

    def get_total_posts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        field_id: int | None,
        user_id: str | None = None,
    ) -> int:
        """
        총 게시글 수를 반환합니다. user_id가 없으면 전체 조회.

        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :param field_id: 필드 ID(없으면 전체).
        :param user_id: 유저 ID(없으면 전체).
        :return: 총 게시글 수.
        """
        total_posts = self._apply_post_filters(
            query=self.db.query(func.count(Posts.url)),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=field_id,
            user_id=user_id,
        ).scalar()
        return int(total_posts or 0)

    def get_user_active_days(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> int:
        """
        유저 기준 활동 일수를 반환합니다.

        :param user_id: 유저 ID.
        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :return: 활동 일수.
        """
        active_days = self._apply_post_filters(
            query=self.db.query(func.count(func.distinct(func.date(Posts.date)))),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=None,
            user_id=user_id,
        ).scalar()
        return int(active_days or 0)

    def get_user_active_months(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> int:
        """
        유저 기준 활동 월 수를 반환합니다.

        :param user_id: 유저 ID.
        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :return: 활동 월 수.
        """
        active_months = self._apply_post_filters(
            query=self.db.query(func.count(func.distinct(func.date_trunc("month", Posts.date)))),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=None,
            user_id=user_id,
        ).scalar()
        return int(active_months or 0)

    def get_user_first_and_latest_post_dates(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> tuple[date | None, date | None]:
        """
        유저의 최초/최신 게시일을 조회합니다.

        :param user_id: 유저 ID.
        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :return: (최초 게시일, 최신 게시일).
        """
        first_datetime, latest_datetime = self._apply_post_filters(
            query=self.db.query(func.min(Posts.date), func.max(Posts.date)),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            field_id=None,
            user_id=user_id,
        ).one()
        first_post_date = first_datetime.date() if first_datetime is not None else None
        latest_post_date = latest_datetime.date() if latest_datetime is not None else None
        return first_post_date, latest_post_date

    def get_user_primary_field_id(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> int | None:
        """
        유저의 대표 field_id를 조회합니다.

        :param user_id: 유저 ID.
        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :return: 대표 field_id 또는 None.
        """
        field_post_count = func.count(Posts.url)
        row = (
            self._apply_post_filters(
                query=self.db.query(Posts.field_id, field_post_count.label("count")).filter(
                    Posts.field_id.isnot(None)
                ),
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                field_id=None,
                user_id=user_id,
            )
            .group_by(Posts.field_id)
            .order_by(field_post_count.desc(), Posts.field_id.asc())
            .first()
        )
        if row is None:
            return None
        return int(row[0])

    def get_user_ranking(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> tuple[int, int]:
        """
        유저 랭킹과 전체 사용자 수를 조회합니다.

        :param user_id: 유저 ID.
        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :return: (rank, total_user).
        """
        user_count_subquery = (
            self.db.query(
                Posts.user_id.label("user_id"),
                func.count(Posts.url).label("post_count"),
            )
            .filter(Posts.date >= start_datetime, Posts.date <= end_datetime)
            .group_by(Posts.user_id)
            .subquery()
        )

        user_post_count = (
            self.db.query(user_count_subquery.c.post_count)
            .filter(user_count_subquery.c.user_id == user_id)
            .scalar()
        )
        normalized_user_post_count = int(user_post_count or 0)

        higher_user_count = (
            self.db.query(func.count())
            .select_from(user_count_subquery)
            .filter(user_count_subquery.c.post_count > normalized_user_post_count)
            .scalar()
        )

        active_user_count = (
            self.db.query(func.count())
            .select_from(user_count_subquery)
            .scalar()
        )
        total_user = int(active_user_count or 0)
        if total_user == 0:
            return 1, 1
        rank = int(higher_user_count or 0) + 1
        return rank, total_user

    def get_category_counts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        field_id: int | None,
        user_id: str | None = None,
    ) -> list[tuple[str, int]]:
        """
        카테고리별 게시글 수를 조회합니다. user_id가 없으면 전체 조회.

        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :param field_id: 필드 ID(없으면 전체).
        :param user_id: 유저 ID(없으면 전체).
        :return: (카테고리, 개수) 목록.
        """
        category_count = func.count(Posts.url)
        rows = (
            self._apply_post_filters(
                query=self.db.query(Posts.category, category_count.label("count")),
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                field_id=field_id,
                user_id=user_id,
            )
            .group_by(Posts.category)
            .order_by(category_count.desc(), Posts.category.asc())
            .all()
        )
        return [
            (str(category), int(count))
            for category, count in rows
            if category is not None
        ]

    def get_keyword_counts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        field_id: int | None,
        user_id: str | None = None,
    ) -> list[tuple[str, int]]:
        """
        키워드별 등장 횟수를 조회합니다. user_id가 없으면 전체 조회.

        :param start_datetime: 시작 일시.
        :param end_datetime: 종료 일시.
        :param field_id: 필드 ID(없으면 전체).
        :param user_id: 유저 ID(없으면 전체).
        :return: (키워드, 개수) 목록.
        """
        keyword_count = func.count(POST_KEYWORD.keyword_id)
        rows = (
            self._apply_post_filters(
                query=(
                    self.db.query(Keyword.keyword, keyword_count.label("count"))
                    .join(POST_KEYWORD, Keyword.id == POST_KEYWORD.keyword_id)
                    .join(
                        Posts,
                        and_(
                            Posts.url == POST_KEYWORD.url,
                            Posts.user_id == POST_KEYWORD.user_id,
                            Posts.platform_id == POST_KEYWORD.platform_id,
                        ),
                    )
                ),
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                field_id=field_id,
                user_id=user_id,
            )
            .group_by(Keyword.keyword)
            .order_by(keyword_count.desc(), Keyword.keyword.asc())
            .all()
        )
        return [
            (str(keyword), int(count)) for keyword, count in rows if keyword is not None
        ]
