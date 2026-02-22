from datetime import date
from typing import List
from pydantic import BaseModel


class _CategoryCount(BaseModel):
    category: str
    count: int


class UserStatResponse(BaseModel):
    duration: int
    category: List[_CategoryCount]
    count: int
    created_at: date
