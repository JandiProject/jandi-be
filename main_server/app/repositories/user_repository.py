from sqlalchemy.orm import Session
from typing import List

from app.models.user_models import User, AuthUser, Fields, UserField, UserStat
from app.models.platform_models import UserPlatform, UserPlatformVerification
from app.models.post_models import Posts, POST_AGG


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.user_id == user_id).first()

    def update_user_profile(
        self,
        user: User,
        name: str,
        notify_email: bool,
        is_public: bool,
        color_theme: str,
    ) -> None:
        user.name = name
        user.notify_email = notify_email
        user.is_public = is_public
        user.color_theme = color_theme

    def get_user_interests(self, user_id: str) -> List[str]:
        results = (
            self.db.query(Fields.field_name)
            .join(UserField, UserField.field_id == Fields.field_id)
            .filter(UserField.user_id == user_id)
            .all()
        )
        return [row.field_name for row in results]

    def get_fields_by_names(self, names: List[str]) -> List[Fields]:
        return self.db.query(Fields).filter(Fields.field_name.in_(names)).all()

    def replace_user_interests(self, user_id: str, field_ids: List[int]) -> None:
        self.db.query(UserField).filter(UserField.user_id == user_id).delete()
        for fid in field_ids:
            self.db.add(UserField(user_id=user_id, field_id=fid))

    def get_auth_user_by_user_id(self, user_id: str) -> AuthUser | None:
        return self.db.query(AuthUser).filter(AuthUser.user_id == user_id).first()

    def delete_user_cascade(self, user_id: str) -> None:
        # FK cascade 미설정 테이블을 의존 순서로 직접 삭제
        self.db.query(POST_AGG).filter(POST_AGG.user_id == user_id).delete()
        # POST_KEYWORDS는 POSTS에 DB CASCADE가 걸려있어 자동 삭제
        self.db.query(Posts).filter(Posts.user_id == user_id).delete()
        self.db.query(UserStat).filter(UserStat.user_id == user_id).delete()
        self.db.query(UserPlatformVerification).filter(UserPlatformVerification.user_id == user_id).delete()
        self.db.query(UserPlatform).filter(UserPlatform.user_id == user_id).delete()
        self.db.query(AuthUser).filter(AuthUser.user_id == user_id).delete()
        # USER_FIELDS는 DB CASCADE로 자동 삭제
        self.db.query(User).filter(User.user_id == user_id).delete()
