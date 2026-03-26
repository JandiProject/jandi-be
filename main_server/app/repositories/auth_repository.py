from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user_models import User, AuthUser

class AuthRepository:
    def __init__(self, db):
        """
        인증 관련 데이터베이스 접근을 위한 저장소 초기화

        :param db: SQLAlchemy 데이터베이스 세션
        :type db: Session
        """
        self.db = db

    def get_user_by_email(self, email: str):
        """
        이메일을 통해 사용자 정보를 조회.

        :param email: 조회할 사용자의 이메일
        :type email: str
        :return: 조회된 유저 객체 또는 None
        :rtype: User | None
        """
        
        return self.db.query(User).filter(User.email == email).first()
    
    def get_auth_user_by_id(self, user_id:str):
        """
        사용자 ID를 통해 인증 정보를 조회.

        :param user_id: 유저의 고유 식별자
        :type user_id: str
        :return: 조회된 인증 정보 객체 또는 None
        :rtype: AuthUser | None
        """
        return self.db.query(AuthUser).filter(AuthUser.user_id == user_id).first()
    
    def create_user(self, email:str, name:str):
        """
        새로운 유저 기본 정보를 생성. (flush를 통해 ID를 생성함)

        :param email: 유저 이메일
        :type email: str
        :param name: 유저 이름
        :type name: str
        :return: 생성된 유저 객체
        :rtype: User
        """
        new_user = User(email=email, name=name)
        self.db.add(new_user)
        self.db.flush()  # user_id생성 위해 flush
        return new_user
    
    def create_auth_user(self, shadow:AuthUser):
        """
        유저의 인증 정보(비밀번호, 토큰 등)를 저장.

        :param shadow: 저장할 인증 정보 객체
        :type shadow: AuthUser
        """
        self.db.add(shadow)
        self.db.commit()

    def commit(self):
        """
        현재 세션의 변경사항을 확정(Commit).
        """
        self.db.commit()

    def refresh_user_stat(self):
        """
        통계용 Materialized View를 갱신.
        """
        self.db.execute(text('REFRESH MATERIALIZED VIEW "USER_STAT"'))
        self.db.commit()

    
