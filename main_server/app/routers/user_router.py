from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.verify_jwt import get_current_user_id
from app.dependencies.database import get_db
from app.models.platform_models import Platform
from app.models.post_models import Posts
from app.models.user_models import UserStat
from app.repositories.user_repository import UserRepository
from app.schemas.analytics_schemas import UserStatResponse
from app.schemas.post_schemas import Post
from app.schemas.user_schemas import (
    DeleteAccountRequest,
    InterestsResponse,
    InterestsUpdateRequest,
    InterestsUpdateResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix='/api/user')


@router.get("/stats", response_model=UserStatResponse)
def get_user_stats(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    user_stats: List[UserStat] = db.query(UserStat).filter(UserStat.user_id == user_id).all()
    if user_stats is None:
        raise HTTPException(status_code=404, detail="User stats not found")
    elif len(user_stats) == 0:
        raise HTTPException(status_code=404, detail="User stats not found")
    else:
        return UserStatResponse(
            duration=(date.today() - user_stats[0].created_at).days,
            category=[{"category": stat.category, "count": stat.count} for stat in user_stats] if user_stats[0].category is not None else [],
            created_at=user_stats[0].created_at,
            count=sum(stat.count for stat in user_stats)
        )


@router.get("/posts", response_model=list[Post])
def get_user_posts(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    category: str | None = None
):
    if category is None:
        posts: list[Post] = db.query(Posts, Platform).filter(Posts.user_id == user_id, Posts.platform_id == Platform.platform_id).all()
    else:
        posts: list[Post] = db.query(Posts, Platform).filter(Posts.user_id == user_id, Posts.category == category, Posts.platform_id == Platform.platform_id).all()
    return map(lambda row: Post(url=row[0].url, category=row[0].category, date=row[0].date.strftime("%Y-%m-%d"), title=row[0].title, platform=row[1].name), posts)


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> ProfileResponse:
    return UserService(UserRepository(db)).get_profile(user_id)


@router.patch("/profile", response_model=ProfileUpdateResponse)
def update_profile(
    data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> ProfileUpdateResponse:
    return UserService(UserRepository(db)).update_profile(db, user_id, data)


@router.get("/interests", response_model=InterestsResponse)
def get_interests(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> InterestsResponse:
    return UserService(UserRepository(db)).get_interests(user_id)


@router.patch("/interests", response_model=InterestsUpdateResponse)
def update_interests(
    data: InterestsUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> InterestsUpdateResponse:
    return UserService(UserRepository(db)).update_interests(db, user_id, data)


@router.delete("", status_code=204)
def delete_account(
    data: DeleteAccountRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> Response:
    UserService(UserRepository(db)).delete_account(db, user_id, data.password)
    return Response(status_code=204)
