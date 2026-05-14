from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.schemas.auth_schemas import *
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.get("/check-email", response_model=EmailCheckResponse)
async def check_email(email: EmailStr = Query(...), db: Session = Depends(get_db)):
    """
    이메일 중복 검사를 수행합니다.

    :param email: 사용자가 입력한 이메일 주소
    :type email: EmailStr
    :param db: 데이터베이스 세션 (Depends 주입)
    :type db: Session
    :return: 사용 가능 여부 결과
    """
    return await AuthService(AuthRepository(db)).check_email_availability(email)

@router.post("/signup", status_code=201, response_model=SignUpResponse)
async def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    """
    회원가입을 진행하고 인증 메일을 발송합니다.

    :param data: 이메일, 비밀번호, 이름이 포함된 요청 바디
    :type data: SignUpRequest
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 가입 처리 상세 정보
    """
    return await AuthService(AuthRepository(db)).register_user(data)

@router.get("/is-verified", response_model=VerificationStatusResponse)
async def is_verified(email: EmailStr = Query(...), db: Session = Depends(get_db)):
    """
    사용자의 이메일 인증 여부를 확인합니다.

    :param email: 조회할 사용자의 이메일
    :type email: EmailStr
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 인증 완료 여부 (bool)
    """
    return await AuthService(AuthRepository(db)).get_verification_status(email)

@router.post("/resend-email")
async def resend_email(email: EmailStr = Query(...), db: Session = Depends(get_db)):
    """
    미인증 사용자의 이메일로 인증 메일을 재전송합니다.

    :param email: 인증 메일을 다시 보낼 이메일 주소
    :type email: EmailStr
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 재전송 결과 메시지
    """
    return await AuthService(AuthRepository(db)).resend_verification(email)

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    """
    이메일 인증 링크 클릭 시 토큰을 검증하고 결과 페이지 보여줌.

    :param token: 이메일에 포함된 JWT 인증 토큰
    :type token: str
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 인증 성공 시 html 페이지 반환
    :rtype: HTMLResponse
    """
    service = AuthService(AuthRepository(db))
    return await service.verify_email_token(token)

@router.post("/signin", response_model=SignInResponse)
async def signin(data: SignInRequest, db: Session = Depends(get_db)):
    """
    로그인을 시도하고 토큰을 발급받습니다.

    :param data: 이메일과 비밀번호 정보
    :type data: SignInRequest
    :param db: 데이터베이스 세션
    :type db: Session
    :return: Access 및 Refresh 토큰
    """
    return await AuthService(AuthRepository(db)).login(data)

@router.post("/refresh")
async def refresh_token(data: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    유효한 Refresh 토큰으로 Access 토큰을 갱신합니다.

    :param data: Refresh 토큰이 담긴 요청 바디
    :type data: TokenRefreshRequest
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 새로운 토큰 정보
    """
    return await AuthService(AuthRepository(db)).refresh_access_token(data.refresh_token)

@router.post("/password/reset/request")
async def pw_reset_request(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    비밀번호 재설정을 위한 이메일 발송을 요청합니다.

    :param data: 비밀번호를 잊은 사용자의 이메일
    :type data: PasswordResetRequest
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 발송 결과 메시지
    """
    return await AuthService(AuthRepository(db)).request_pw_reset(data.email)

@router.post("/password/reset/{user_token}", status_code=201)
async def pw_reset_confirm(user_token: str = Path(...), data: PasswordResetConfirm = None, db: Session = Depends(get_db)):
    """
    임시 토큰을 사용하여 새로운 비밀번호를 등록합니다.

    :param user_token: URL 경로에 포함된 30분 유효 임시 토큰
    :type user_token: str
    :param data: 새 비밀번호 데이터
    :type data: PasswordResetConfirm
    :param db: 데이터베이스 세션
    :type db: Session
    :return: 변경 성공 결과
    """
    return await AuthService(AuthRepository(db)).confirm_pw_reset(user_token, data.newPassword)