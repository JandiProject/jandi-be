from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.post_models import POST_AGG

class JandiRepository:
    def __init__(self, db: Session):
        """
        잔디 데이터 접근을 위한 저장소 초기화

        :param db: SQLAlchemy 데이터베이스 세션
        :type db: Session
        """
        self.db = db

    def get_posts_by_date_range(self, user_id: str, start_date: datetime, end_date: datetime) -> list[POST_AGG]:
        """
        특정 기간 동안의 유저 포스트 통계 데이터를 조회합니다.

        :param user_id: 조회할 유저의 ID
        :type user_id: str
        :param start_date: 조회 시작 날짜
        :type start_date: datetime
        :param end_date: 조회 종료 날짜
        :type end_date: datetime
        :return: POST_AGG 모델 객체 리스트
        :rtype: list[POST_AGG]
        """
        return self.db.query(POST_AGG).filter(
            POST_AGG.user_id == user_id,
            POST_AGG.date.between(start_date, end_date)
        ).all()
