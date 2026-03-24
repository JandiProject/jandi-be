from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.schemas.platform_schemas import Platforms


class QueueName(str, Enum):
    PLATFORM_REGISTER = "platform_register"


# TODO: 플랫폼 등록 로직 개선 시 이 메시지 구조는 없앨 예정 (글 하나하나를 MQ로 보내는 것은 비효율적이므로 플랫폼 정보만 보내도록 개선할 예정)
class PlatformRegisterArticleMessage(BaseModel):
    link: str
    user_id: str
    platform: str
    published_at: datetime

# 궁극적으로 이 메시지 사용 예정 (얘는 그냥 유저, 플랫폼, 계정 id 정보만 담은 메시지)
class PlatformRegisterMessage(BaseModel):
    platform_name: Platforms
    account_id: str
    user_id: str