from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.dependencies.database import Base
import uuid

class Platform(Base):
    """플랫폼 정보를 저장하는 테이블"""
    __tablename__ = "PLATFORM"
    
    platform_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True)  

class UserPlatform(Base):
    """유저와 플랫폼 간의 매핑 정보를 저장하는 테이블"""
    __tablename__ = "USER_PLATFORM"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
    platform_id = Column(Integer, ForeignKey("PLATFORM.platform_id"), primary_key=True)
    
    account_id = Column("id", String(255)) 
    last_upload = Column(DateTime, nullable=True)