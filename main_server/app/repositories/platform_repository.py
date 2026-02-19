from sqlalchemy import Column
from app.models.post_models import Posts
from app.models.user_models import Platform, UserPlatform
from sqlalchemy.orm import Session


class PlatformRepository:
    def __init__(self, db):
        self.db: Session = db

    def get_platform_by_name(self, platform_name: str):
        """
        플랫폼 이름을 기반으로 플랫폼 정보를 조회하는 함수
        """
        return self.db.query(Platform).filter(Platform.name == platform_name).first()

    def get_user_platform_mapping(self, user_id: str, platform_id: Column) -> UserPlatform|None:
        """
        특정 유저의 특정 플랫폼에 대한 매핑 정보 조회
        
        :param self: 
        :param user_id: 조회할 유저의 ID
        :type user_id: str
        :param platform_id: 조회할 플랫폼의 ID
        :type platform_id: Column
        :return: 유저-플랫폼 매핑 정보 (존재하지 않으면 None)
        :rtype: UserPlatform | None
        """
        return self.db.query(UserPlatform).filter(
            UserPlatform.user_id == user_id,
            UserPlatform.platform_id == platform_id,
        ).first()

    def create_user_platform_mapping(self, user_id: str, platform_id: Column, account_id: str) -> UserPlatform:
        """
        새로운 유저-플랫폼 매핑을 생성하는 함수
        
        :param self: 
        :param user_id: 매핑을 생성할 유저의 ID
        :type user_id: str
        :param platform_id: 매핑을 생성할 플랫폼의 ID
        :type platform_id: Column
        :param account_id: 매핑에 사용할 계정 ID
        :type account_id: str
        """
        new_mapping = UserPlatform(user_id=user_id, platform_id=platform_id, account_id=account_id)
        self.db.add(new_mapping)
        return new_mapping

    def update_user_platform_account(self, user_platform: UserPlatform, account_id: str):
        """
        유저 플랫폼 매핑의 계정 ID를 업데이트하는 함수
        
        :param self: 
        :param user_platform: 업데이트할 유저-플랫폼 매핑 정보
        :type user_platform: UserPlatform
        :param account_id: 새로운 계정 ID
        :type account_id: str
        """
        user_platform.account_id = account_id  # type: ignore

    def get_posts_by_user_and_platform(self, user_id: str, platform_id: Column) -> list[Posts]:
        """
        특정 유저와 플랫폼에 해당하는 게시글 정보를 조회하는 함수
        
        :param self: 
        :param user_id: 조회할 유저의 ID
        :type user_id: str
        :param platform_id: 조회할 플랫폼의 ID
        :type platform_id: Column
        :return: 해당 유저와 플랫폼에 대한 게시글 목록
        :rtype: list[Posts]
        """
        return self.db.query(Posts).filter(
            Posts.user_id == user_id,
            Posts.platform_id == platform_id,
        ).all()

    def delete_post(self, post: Posts):
        self.db.delete(post)

    def delete_user_platform_mapping(self, user_platform: UserPlatform):
        self.db.delete(user_platform)

    def get_user_platforms_with_platform(self, user_id: str):
        return self.db.query(UserPlatform, Platform).filter(
            UserPlatform.platform_id == Platform.platform_id,
            UserPlatform.user_id == user_id,
        ).all()


