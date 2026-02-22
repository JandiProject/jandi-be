from pydantic import BaseModel


class Post(BaseModel):
    url: str
    category: str
    date: str
    title: str
    platform: str
