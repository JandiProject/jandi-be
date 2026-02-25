from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.schemas.jandi_schemas import GetJandiResponse
from app.models.post_models import POST_AGG


def get_jandi_data(db: Session, user_id: str) -> list[GetJandiResponse]:
    posts: list[POST_AGG] = db.query(POST_AGG).filter(POST_AGG.user_id == user_id, POST_AGG.date.between(datetime.now() - timedelta(days=365), datetime.now())).all()
    if len(posts) == 0:
        return []
    # 그걸 [GetJandiResponse]로 변환
    response = [GetJandiResponse(date=post.date.strftime("%Y-%m-%d"), category=post.category, count=post.count) for post in posts] # pyright: ignore[reportArgumentType]
    return response
    