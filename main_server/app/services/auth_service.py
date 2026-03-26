from datetime import datetime, timedelta
import jwt
import os
from fastapi import HTTPException
from app.dependencies.database import get_db
from app.models.user_models import User, AuthUser
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from app.schemas.auth_schemas import SignUpRequest, SignInRequest, SignInResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

class AuthService:
    def __init__(self, repository):
        """
        인증 관련 비즈니스 로직 서비스를 초기화.

        :param repository: DB 접근을 담당하는 저장소 객체
        :type repository: AuthRepository
        """
        self.repository = repository

    async def register_new_user(self, data:SignUpRequest):

        """
        신규 유저 등록 및 이메일 인증 발송 프로세스를 처리.

        :param data: 검증된 회원가입 요청 데이터
        :type data: SignUpRequest
        :return: 성공 메시지 딕셔너리
        :rtype: dict
        :raises HTTPException: 이미 이메일이 존재할 경우 발생
        """
        
        #1. 중복검사
        '#TODO: /api/auth/check-email로 중복 검사 api 제작'
    
        if self.repository.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
        #2. User 생성
        new_user = self.repository.create_user(data.email, data.name)

        #3. 비밀번호 해시 및 토큰 생성
        hashed_pw = pwd_context.hash(data.password)
        verify_token = jwt.encode(
            {"sub" : str(new_user.user_id), "exp":datetime.now(datetime.timezone.utc) + timedelta(hours=1)},
            SECRET_KEY, algorithm = ALGORITHM
        )

        #AuthUser 생성 및 저장
        shadow = AuthUser(
            user_id = new_user.user_id,
            emial = data.email,
            hashed_password = hashed_pw,
            is_verified=False,
            verification_token=verify_token
        )
        self.repository.create_auth_user(shadow)

        #5. 이메일 발송
        await send_verification_email(data.email, verify_token)
        return {"message" : "회원가입 완료! 이메일을 확인해주세요."}
    
    def verify_email(self, token:str):

        """
        메일 인증 토큰의 유효성을 검증하고 계정을 활성화.

        :param token: 이메일로 발송된 JWT 인증 토큰
        :type token: str
        :return: 인증 완료 메시지
        :rtype: dict
        :raises HTTPException: 토큰 만료 또는 유효하지 않을 때 발생
        """
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code = 400, detail="토큰이 만료되었습니다")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=40, detail="유효하지 않은 토큰입니다")
        
        shadow = self.repository.get_auth_user_by_id(user_id)
        if not shadow or shadow.verification_token != token:
            raise HTTPException(status_code=400, detail="인증 정보가 올바르지 않습니다")
        
        shadow.is_verified=True
        shadow.verification_token = None
        self.repository.commit()
        self.repository.refresh_user_stat()
        return{"message" : "이메일 인증 완료!"}
    
    def sign_in(self, data: SignInRequest):

        """
        사용자 자격 증명을 확인하고 서비스 이용 토큰을 발급.

        :param data: 로그인 요청 데이터 (이메일, 비번)
        :type data: SignInRequest
        :return: 엑세스 토큰 정보
        :rtype: dict
        :raises HTTPException: 인증 실패 또는 미인증 계정일 때 발생
        """

        user = self.repository.get_user_by_email(data.email)
        '#TODO: CIA triad에서 사용자 존재 여부를 드러내는 것은 기밀성을 떨어트릴 수 있습니다. '
        '#TODO: 이메일 존재 여부와 비밀번호 일치 여부를 나타내는 대신 이메일과 비밀번호가 일치하지 않는다 정도로 보여주는 건 어떨까요?  '
        if not user:
            raise HTTPException(status_code=400, detail="존재하지 않는 이메일입니다")
        shadow = self.repository.get_auth_user_by_id(user, user_id)
        if not shadow or not pwd_context.verify(data.password, shadow.hashed_password):
            raise HTTPException(status_code=400, detail="비밀번호가 일치")
        
        if user.email != shadow.email:
            user.email = shadow.email
            self.repository.commit()

        token = jwt.encode(
            {"sub": str(user.user_id), "exp": datetime.utcnow() + timedelta(days=7)},
            SECRET_KEY, algorithm=ALGORITHM
        )
        return {"access_token": token}
        
        


