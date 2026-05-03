import re
from datetime import datetime

from pydantic import BaseModel, field_validator


class ProfileResponse(BaseModel):
    name: str
    notifyEmail: bool
    publicJandi: bool


class ProfileUpdateRequest(BaseModel):
    name: str
    notifyEmail: bool
    publishJandi: bool
    color_theme: str

    @field_validator("color_theme")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError("color_theme은 #RRGGBB 형식의 hex 코드여야 합니다.")
        return v


class ProfileUpdateResponse(BaseModel):
    name: str
    notifyEmail: bool
    publishJandi: bool
    updated_at: datetime
    color_theme: str


class InterestsResponse(BaseModel):
    interests: list[str]


class InterestsUpdateRequest(BaseModel):
    interests: list[str]


class InterestsUpdateResponse(BaseModel):
    interests: list[str]
    updated_at: datetime


class DeleteAccountRequest(BaseModel):
    password: str
