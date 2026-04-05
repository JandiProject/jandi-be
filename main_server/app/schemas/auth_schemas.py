# Pydantic Models : 값을 쿼리가 아닌 json으로 넘겨주기 위해

import re
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

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
        # Minimum 8 characters, at least one uppercase, one lowercase, one digit, one special character
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




class SignInRequest(BaseModel):
    """
    로그인 요청 모델
    """
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    """토큰 재발급 요청 모델"""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 모델"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """새 비밀번호 등록 모델"""
    newPassword: str

class EmailCheckResponse(BaseModel):
    """이메일 중복 확인 응답 모델"""
    available: bool
    message: str

class VerificationStatusResponse(BaseModel):
    """이메일 인증 여부 조회 응답 모델"""
    is_verified: bool