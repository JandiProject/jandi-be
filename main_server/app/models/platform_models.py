from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.dependencies.database import Base
from datetime import datetime
import uuid

class Platform(Base):
    """플랫폼 정보를 저장하는 테이블"""
    __tablename__ = "PLATFORM"
    
    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True)  

class UserPlatform(Base):
    """유저와 플랫폼 간의 매핑 정보를 저장하는 테이블"""
    __tablename__ = "USER_PLATFORM"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("PLATFORM.platform_id"), primary_key=True)
    
    account_id = Column("id", String(255)) 
    last_upload = Column(DateTime, nullable=True)

class UserPlatformVerification(Base):
    __tablename__ = "user_platform_verification"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("PLATFORM.platform_id"), primary_key=True)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    # 인증 완료 전 요청한 블로그 계정(naver/tistory 공통)
    pending_account_id = Column(String(255), nullable=True)