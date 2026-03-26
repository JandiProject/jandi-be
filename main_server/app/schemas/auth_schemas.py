# Pydantic Models : 값을 쿼리가 아닌 json으로 넘겨주기 위해

import re
from pydantic import BaseModel, EmailStr, field_validator


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
