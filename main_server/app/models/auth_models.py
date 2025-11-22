from pydantic import BaseModel, EmailStr, validator
import re

class SignInRequest(BaseModel):
    """
    Request model for signing in.
    Note: Passwords should be transmitted over HTTPS only.
    """
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        # Minimum 8 characters, at least one uppercase, one lowercase, one digit, one special character
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
class SignInResponse(BaseModel):
    access_token: str