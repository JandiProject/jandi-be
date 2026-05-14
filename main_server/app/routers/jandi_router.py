from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.core.verify_jwt import get_current_user_id
from app.schemas.jandi_schemas import GetJandiResponse, GetSignedUrlResponse
from app.repositories.jandi_repository import JandiRepository
from app.services.jandi_service import JandiService

router = APIRouter(prefix='/api/jandi', tags=['Jandi'])

@router.get("/", response_model=list[GetJandiResponse])
def read_jandi_data(date: str | None = None, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    유저의 잔디 데이터를 조회합니다.

    :param date: 기준 날짜 (YYYY-MM-DD)
    :type date: str | None
    :param db: 데이터베이스 세션
    :type db: Session
    :param user_id: 현재 인증된 유저의 ID
    :type user_id: str
    :return: 잔디 통계 데이터 리스트
    """
    repo = JandiRepository(db)
    service = JandiService(repo)
    return service.get_user_jandi_data(user_id, end_date=date)

@router.get("/signedUrl", response_model=GetSignedUrlResponse)
def read_signed_url(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    위젯용 서명된 URL을 생성하여 반환합니다.

    :param db: 데이터베이스 세션
    :type db: Session
    :param user_id: 현재 인증된 유저의 ID
    :type user_id: str
    :return: 위젯 URL 정보
    """
    repo = JandiRepository(db)
    service = JandiService(repo)
    return service.generate_signed_url(user_id)

@router.get("/widget")
def read_jandi_widget(token: str | None = None, db: Session = Depends(get_db)):
    """
    외부 위젯용 HTML 페이지를 반환합니다.

    :param token: 위젯 인증 토큰 (Query parameter)
    :type token: str | None
    :param db: 데이터베이스 세션
    :type db: Session
    :return: HTMLResponse 위젯 페이지
    """
    repo = JandiRepository(db)
    service = JandiService(repo)
    return service.get_jandi_widget_html(token)