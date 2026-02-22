from pydantic import BaseModel


class JandiBaseSchema(BaseModel):
    pass


class GetJandiResponse(BaseModel):
    date: str
    topic: str
    count: int
