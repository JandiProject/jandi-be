import re
from pydantic import BaseModel, EmailStr, validator


class AuthBaseSchema(BaseModel):
    pass


class SignInRequest(BaseModel):
    """
    Request model for signing in.
    Note: Passwords should be transmitted over HTTPS only.
    """

    email: EmailStr
    password: str

    @validator("password")
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
    access_token: str
