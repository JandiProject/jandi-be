from pydantic import BaseModel


class JandiBaseSchema(BaseModel):
    pass


class GetJandiResponse(BaseModel):
    """잔디 데이터 응답 모델"""
    date: str
    category: str
    count: int

class GetSignedUrlRequest(BaseModel):
    """서명된 URL 응답 모델"""
    url: str