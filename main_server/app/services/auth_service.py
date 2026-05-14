import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from passlib.context import CryptContext
from app.schemas.auth_schemas import *
from app.services.email_service import send_verification_email, send_password_reset_email
from app.models.user_models import User, AuthUser
from fastapi.responses import HTMLResponse
from app.templates.email_templates import get_verification_html, get_verify_success_page_html, get_password_reset_html

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET", "jandi_secret_key")
ALGORITHM = "HS256"

class AuthService:
    def __init__(self, repository):
        """
        인증 관련 비즈니스 로직 서비스를 초기화합니다.

        :param repository: 데이터베이스 접근을 담당하는 저장소 객체
        :type repository: AuthRepository
        """
        self.repository = repository

    def _generate_token(self, payload: dict, expires_delta: timedelta) -> str:
        """
        내부적으로 사용하는 JWT 토큰 생성 유틸리티입니다.

        :param payload: 토큰에 담을 데이터 내용
        :type payload: dict
        :param expires_delta: 토큰의 유효 기간
        :type expires_delta: timedelta
        :return: 인코딩된 JWT 토큰 문자열
        :rtype: str
        """
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    async def check_email_availability(self, email: str) -> dict:
        """
        회원가입 전 이메일의 중복 여부를 확인합니다.

        :param email: 중복 확인을 진행할 사용자의 이메일
        :type email: str
        :return: 사용 가능 여부와 안내 메시지
        :rtype: dict
        """
        user = self.repository.get_user_by_email(email)
        if user:
            return {"available": False, "message": "이미 존재하는 이메일입니다."}
        return {"available": True, "message": "사용 가능한 이메일입니다."}

    async def register_user(self, data: SignUpRequest) -> SignUpResponse:
        """
        신규 유저를 등록하고 1시간 유효한 인증 메일을 발송합니다.

        :param data: 회원가입에 필요한 유저 정보 (email, password, name)
        :type data: SignUpRequest
        :return: 가입 정보 및 인증 만료 시간을 포함한 응답 객체
        :rtype: SignUpResponse
        :raises HTTPException: 이미 가입된 이메일일 경우 409 Conflict 발생
        """
        if self.repository.get_user_by_email(data.email):
            raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

        user = self.repository.create_user(data.email, data.name)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        verify_token = self._generate_token({"sub": str(user.user_id), "type": "verify"}, timedelta(hours=1))

        shadow = AuthUser(
            user_id=user.user_id,
            email=data.email,
            hashed_password=pwd_context.hash(data.password),
            is_verified=False,
            verification_token=verify_token
        )
        self.repository.create_auth_user(shadow)
        await send_verification_email(data.email, verify_token)
        return SignUpResponse(message="회원가입 성공", email=data.email, verification_status= "pending",expires_at=expires_at)

    async def get_verification_status(self, email: str) -> dict:
        """
        특정 이메일의 인증 완료 여부를 조회합니다.

        :param email: 조회를 원하는 사용자의 이메일
        :type email: str
        :return: 인증 여부 (True/False)
        :rtype: dict
        :raises HTTPException: 존재하지 않는 유저일 경우 404 Not Found 발생
        """
        user = self.repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        shadow = self.repository.get_auth_user_by_id(user.user_id)
        return {"is_verified": shadow.is_verified if shadow else False}

    async def resend_verification(self, email: str) -> dict:
        """
        인증 메일을 재전송합니다. 보안을 위해 유저 존재 여부와 관계없이 성공 응답을 반환합니다.

        :param email: 인증 메일을 다시 받을 사용자의 이메일
        :type email: str
        :return: 재전송 성공 메시지
        :rtype: dict
        """
        user = self.repository.get_user_by_email(email)
        if user:
            shadow = self.repository.get_auth_user_by_id(user.user_id)
            if shadow and not shadow.is_verified:
                token = self._generate_token({"sub": str(user.user_id), "type": "verify"}, timedelta(hours=1))
                shadow.verification_token = token
                self.repository.commit()
                await send_verification_email(email, token)
        return {"message": "인증 메일이 재전송되었습니다."}

    async def verify_email_token(self, token: str)-> HTMLResponse:
        """
        이메일 인증 토큰을 검증하고 사용자의 인증 상태를 활성화한 뒤 성공 HTML 페이지를 반환합니다.

        :param token: 이메일 링크에 포함된 JWT 인증 토큰
        :type token: str
        :return: 브라우저에서 렌더링될 HTML 페이지
        :rtype: HTMLResponse
        :raises HTTPException: 잘못된 형식의 토큰일 경우 400 Bad Request 발생
        :raises HTTPException: 토큰 만료 또는 변조된 경우 401 Unauthorized 발생
        :raises HTTPException: 해당 유저 정보를 찾을 수 없을 경우 404 Not Found 발생
        :raises HTTPException: 이미 인증이 완료된 유저일 경우 409 Conflict 발생
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "verify":
                raise HTTPException(status_code=400, detail="잘못된 용도의 토큰입니다.")
            user_id = payload["sub"]
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰입니다.")
        
        shadow = self.repository.get_auth_user_by_id(user_id)
        if not shadow: raise HTTPException(status_code=404, detail="정보를 찾을 수 없습니다.")

        if shadow.is_verified:
            raise HTTPException(status_code=409, detail="이미 인증이 완료된 계정입니다.")
        
        shadow.is_verified = True
        shadow.verification_token = None
        self.repository.commit()

        html_content = get_verify_success_page_html()
        return HTMLResponse(content=html_content, status_code=200)

    async def login(self, data: SignInRequest) -> SignInResponse:
        """
        로그인을 처리하고 Access 및 Refresh 토큰을 발급합니다. 사유별 명확한 에러를 반환합니다.

        :param data: 로그인 요청 정보 (email, password)
        :type data: SignInRequest
        :return: Access 및 Refresh 토큰 객체
        :rtype: SignInResponse
        :raises HTTPException: 이메일 미존재(400), 비밀번호 불일치(400), 미인증 계정(403) 발생
        """
        user = self.repository.get_user_by_email(data.email)
        if not user:
            raise HTTPException(status_code=401, detail="존재하지 않는 이메일입니다.")
        
        shadow = self.repository.get_auth_user_by_id(user.user_id)
        if not shadow or not pwd_context.verify(data.password, shadow.hashed_password):
            raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
            
        if not shadow.is_verified:
            raise HTTPException(status_code=403, detail="이메일 인증이 필요합니다.")

        access = self._generate_token({"sub": str(user.user_id), "scope": "access"}, timedelta(hours=2))
        refresh = self._generate_token({"sub": str(user.user_id), "scope": "refresh"}, timedelta(days=7))
        return SignInResponse(access_token=access, refresh_token=refresh)

    async def refresh_access_token(self, refresh_token: str) -> TokenRefreshResponse:
        """
        유효한 Refresh 토큰을 사용하여 새로운 Access 토큰을 발급합니다.

        :param refresh_token: 사용자가 보유한 Refresh 토큰
        :type refresh_token: str
        :return: 새로 발급된 Access 토큰 정보
        :rtype: TokenRefreshResponse응답모델
        :raises HTTPException: 토큰이 유효하지 않거나 만료된 경우 401 Unauthorized 발생
        :raises HTTPException: 인증되지 않았거나 차단된 유저일 경우 403 Forbidden 발생
        """
        try:
            # 1. 토큰 디코딩
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
            # 2. Signin에서 "scope": "refresh"로 넣었는지 확인하세요!
            if payload.get("scope") != "refresh":
                raise HTTPException(status_code=401, detail="리프레시 토큰이 아닙니다.")
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="토큰 페이로드가 유효하지 않습니다.")
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인하세요.")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

        # 3. 유저 상태 확인 (DB 조회)
        shadow = self.repository.get_auth_user_by_id(user_id)
        if not shadow or not shadow.is_verified:
            raise HTTPException(status_code=403, detail="인증되지 않은 유저이거나 존재하지 않는 유저입니다.")

        #4. 새로운 Access 토큰만 생성해서 반환
        new_access = self._generate_token(
            {"sub": user_id, "scope": "access"}, 
            timedelta(hours=2)
        )
    
        return TokenRefreshResponse(refresh_token=refresh_token, access_token=new_access)

    async def request_pw_reset(self, email: str) -> dict:
        """
        비밀번호 재설정을 위한 30분 유효 임시 토큰 링크를 메일로 발송합니다.

        :param email: 비밀번호를 재설정할 사용자의 이메일
        :type email: str
        :return: 안내 메시지
        :rtype: dict
        """
        user = self.repository.get_user_by_email(email)
        if user:
            token = self._generate_token({"sub": str(user.user_id), "type": "pw_reset"}, timedelta(minutes=30))
            await send_password_reset_email(email, token)
        return {"message": "인증 메일이 전송되었습니다."}

    async def confirm_pw_reset(self, token: str, new_pw: str) -> dict:
        """
        임시 토큰을 확인하고 사용자의 비밀번호를 새로운 해시값으로 업데이트합니다.

        :param token: URL 경로에 포함된 30분 유효 임시 토큰
        :type token: str
        :param new_pw: 새로 등록할 비밀번호 원문
        :type new_pw: str
        :return: 성공 확인 메시지
        :rtype: dict
        :raises HTTPException: 잘못된 토큰 형식일 경우 400 Bad Request 발생
        :raises HTTPException: 토큰 만료 또는 변조 시 401 Unauthorized 발생
        :raises HTTPException: 유저 정보를 찾을 수 없을 경우 404 Not Found 발생
        :raises HTTPException: 기존 비밀번호와 동일할 경우 409 Conflict 발생
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "pw_reset": 
                raise ValueError()
            user_id = payload["sub"]
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="유효기간 만료 혹은 잘못된 토큰입니다.")

        shadow = self.repository.get_auth_user_by_id(user_id)
        # [404 로직] 토큰의 유저는 존재하나 DB에 인증 정보(Shadow)가 없는 경우
        if not shadow:
            raise HTTPException(status_code=404, detail="해당 유저의 인증 정보를 찾을 수 없습니다.")

        # [409 로직] 보안 정책: 기존 비밀번호와 새 비밀번호가 동일한지 체크
        if pwd_context.verify(new_pw, shadow.hashed_password):
            raise HTTPException(status_code=409, detail="기존 비밀번호와 다른 비밀번호를 입력해주세요.")

        # 비밀번호 업데이트
        shadow.hashed_password = pwd_context.hash(new_pw)
    
    
        self.repository.commit()


        '#TODO: 바뀐 새 비밀번호를 평문으로 제시할 경우 패킷 공격에 취약하므로'
        '#TODO: 내부적으로 업데이트, 응답으로는 성공적으로 변경되었음만 알림'
        return {"newPassword": "비밀번호가 성공적으로 변경되었습니다."}