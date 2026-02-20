import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID  # Postgres 전용 UUID 타입
from app.dependencies.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "USER"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255))
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    color_theme = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=False)
    notify_email = Column(Boolean, default=False)
    


class Platform(Base):
    __tablename__ = "PLATFORM"
    
    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True)  

class UserPlatform(Base):
    __tablename__ = "USER_PLATFORM"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("PLATFORM.platform_id"), primary_key=True)
    
    account_id = Column("id", String(255)) 
    last_upload = Column(DateTime, nullable=True)

class AuthUser(Base):
    __tablename__ = "AUTH_USER"

    auth_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), nullable=False)

    email = Column(String(255), nullable=False)
    hashed_password = Column(String, nullable=False)

    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)

class UserStat(Base):
    __tablename__ = "USER_STAT"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
    category = Column(String(255), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    count = Column(Integer, default=0)

# class UserLevel(Base):
#     __tablename__ = "USER_LEVEL"

#     user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id"), primary_key=True)
#     total_count = Column(Integer, default=0)
#     level = Column(String, nullable=True)

class LevelThreshold(Base):
    __tablename__ = "LEVEL_THRESHOLDS"

    level_name = Column(String, primary_key=True)
    min_post = Column(Integer, nullable=False)
class Fields(Base):
    __tablename__ = 'FIELDS'
    field_id = Column(Integer, primary_key=True, autoincrement=True, default=1)
    field_name = Column(String(50), unique=True, nullable=False)

class UserField(Base):
    __tablename__ = 'USER_FIELDS'
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.user_id", ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    field_id = Column(Integer, ForeignKey('FIELDS.field_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)