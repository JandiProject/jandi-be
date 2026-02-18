from pydantic import BaseModel


class UserPlatformRequest(BaseModel):
    platform_name: str
    account_id: str


class UserPlatformResponse(BaseModel):
    status: str
    message: str
    platform: str
    registered_id: str
