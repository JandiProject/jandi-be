# Pydantic Models : 값을 쿼리가 아닌 json으로 넘겨주기 위해

import re
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

# 비밀번호 공통 검증 함수
def validate_password(value: str) -> str:
    """
    비밀번호 유효성 검사 공통 함수:
    8자 이상, 대문자, 소문자, 숫자, 특수문자 포함 여부 확인
    """
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value

class AuthBaseSchema(BaseModel):
    pass


class SignUpRequest(BaseModel):
    """
    회원가입 요청 모델
    (Note: Passwords should be transmitted over HTTPS only.)
    """

    email: EmailStr
    password: str
    name : str


    @field_validator("password") 
    @classmethod
    def password_strength(cls, value):
        return validate_password(value) #공통 함수 호출

class SignUpResponse(BaseModel):
    """회원가입 응답 모델"""
    message: str
    email: str
    verification_status: str = "pending"
    expires_at: datetime

class SignInResponse(BaseModel):
    """
    로그인 응답 모델
    """
    access_token: str
    refresh_token: str




class SignInRequest(BaseModel):
    """
    로그인 요청 모델
    """
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    """토큰 재발급 요청 모델"""
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    """토큰 재발급 응답 모델"""
    '#TODO : 액세스 토큰까지 줘야 되는데 api명세서에 리프레시 토큰만 명시했습니다. 수정하겠습니다.'
    refresh_token: str
    access_token : str


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 모델"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """새 비밀번호 등록 모델"""
    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def password_strength(cls, value):
        # 공통 함수 호출
        return validate_password(value)

class EmailCheckResponse(BaseModel):
    """이메일 중복 확인 응답 모델"""
    available: bool
    message: str

class VerificationStatusResponse(BaseModel):
    """이메일 인증 여부 조회 응답 모델"""
    is_verified: bool