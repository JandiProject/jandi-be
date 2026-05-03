from datetime import datetime

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import (
    InterestsResponse,
    InterestsUpdateRequest,
    InterestsUpdateResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_profile(self, user_id: str) -> ProfileResponse:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return ProfileResponse(
            name=user.name,
            notifyEmail=user.notify_email,
            publicJandi=user.is_public,
        )

    def update_profile(
        self, db: Session, user_id: str, data: ProfileUpdateRequest
    ) -> ProfileUpdateResponse:
        try:
            user = self.repository.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=400, detail="사용자를 찾을 수 없습니다.")
            self.repository.update_user_profile(
                user,
                name=data.name,
                notify_email=data.notifyEmail,
                is_public=data.publishJandi,
                color_theme=data.color_theme,
            )
            db.commit()
            return ProfileUpdateResponse(
                name=user.name,
                notifyEmail=user.notify_email,
                publishJandi=user.is_public,
                updated_at=datetime.utcnow(),
                color_theme=user.color_theme,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="프로필 업데이트 중 오류가 발생했습니다.")

    def get_interests(self, user_id: str) -> InterestsResponse:
        return InterestsResponse(interests=self.repository.get_user_interests(user_id))

    def update_interests(
        self, db: Session, user_id: str, data: InterestsUpdateRequest
    ) -> InterestsUpdateResponse:
        try:
            if not data.interests:
                self.repository.replace_user_interests(user_id, [])
                db.commit()
                return InterestsUpdateResponse(interests=[], updated_at=datetime.utcnow())

            found = self.repository.get_fields_by_names(data.interests)
            found_names = {f.field_name for f in found}
            invalid = [n for n in data.interests if n not in found_names]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"존재하지 않는 관심 분야: {', '.join(invalid)}",
                )

            name_to_id = {f.field_name: f.field_id for f in found}
            self.repository.replace_user_interests(user_id, [name_to_id[n] for n in data.interests])
            db.commit()
            return InterestsUpdateResponse(
                interests=data.interests,
                updated_at=datetime.utcnow(),
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="관심 분야 업데이트 중 오류가 발생했습니다.")

    def delete_account(self, db: Session, user_id: str, password: str) -> None:
        try:
            auth_user = self.repository.get_auth_user_by_user_id(user_id)
            if not auth_user:
                raise HTTPException(status_code=400, detail="인증 정보를 찾을 수 없습니다.")
            if not pwd_context.verify(password, auth_user.hashed_password):
                raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
            self.repository.delete_user_cascade(user_id)
            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="계정 삭제 중 오류가 발생했습니다.")
