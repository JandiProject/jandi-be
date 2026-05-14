import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from app.repositories.jandi_repository import JandiRepository
from app.schemas.jandi_schemas import GetJandiResponse
from app.templates.html_template import get_html_template
from app.core.verify_jwt import get_jandi_user_id

UI_SECRET_KEY = os.getenv("UI_SECRET_KEY", "my_super_secret_key")
ALGORITHM = "HS256"

class JandiService:
    def __init__(self, repository: JandiRepository):
        """
        잔디 비즈니스 로직 서비스를 초기화합니다.

        :param repository: 잔디 데이터 저장소 객체
        :type repository: JandiRepository
        """
        self.repository = repository

    def get_user_jandi_data(self, user_id: str, days: int = 30, end_date: str | None = None) -> list[GetJandiResponse]:
        """
        유저의 최근 잔디 데이터를 조회하여 스키마 형식으로 반환합니다.

        :param user_id: 유저의 고유 식별자
        :type user_id: str
        :param days: 조회할 기간 (일 단위)
        :type days: int
        :param end_date: 조회 종료 기준 날짜 (None이면 오늘)
        :type end_date: str | None
        :return: 검증된 잔디 데이터 리스트
        :rtype: list[GetJandiResponse]
        """
        dt_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        dt_start = dt_end - timedelta(days=days)

        posts = self.repository.get_posts_by_date_range(user_id, dt_start, dt_end)
        
        return [
            GetJandiResponse(
                date=post.date.strftime("%Y-%m-%d"),
                category=post.category,
                count=post.count
            ) for post in posts
        ]

    def generate_signed_url(self, user_id: str) -> dict:
        """
        위젯 접근을 위한 서명된 토큰이 포함된 URL을 생성합니다.

        :param user_id: URL을 생성할 유저의 ID
        :type user_id: str
        :return: 생성된 URL 정보 딕셔너리
        :rtype: dict
        """
        verify_token = jwt.encode({"sub": str(user_id)}, UI_SECRET_KEY, algorithm=ALGORITHM)
        return {"url": f"http://136.110.239.66/api/jandi/widget?token={verify_token}"}

    def get_jandi_widget_html(self, token: str | None) -> HTMLResponse:
        """
        토큰을 검증하고 잔디 위젯용 HTML 응답을 생성합니다.

        :param token: 위젯 인증용 JWT 토큰
        :type token: str | None
        :return: HTML 템플릿 응답
        :rtype: HTMLResponse
        :raises HTTPException: 토큰이 없거나 유효하지 않을 때 발생
        """
        if not token:
            raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
        
        user_id = get_jandi_user_id(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

        # 위젯용 최근 30일 데이터 조회
        data = self.get_user_jandi_data(user_id, days=30)
        formatted_data = [{"date": d.date, "category": d.category, "count": d.count} for d in data]
        
        return HTMLResponse(content=get_html_template(formatted_data), status_code=200)