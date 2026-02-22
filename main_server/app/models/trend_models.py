from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from app.dependencies.database import Base

class Keyword(Base):
    __tablename__ = 'KEYWORDS'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), unique=True, nullable=False) # 중복 방지
    
    # 유사어 통합용 (예: k8s의 master_id를 Kubernetes의 id로 설정)
    master_id = Column(Integer, ForeignKey('KEYWORDS.id'), nullable=True)

class ExternalPost(Base):
    __tablename__ = 'EXTERNAL_POSTS'
    id = Column(String(64), primary_key=True) # URL 해시값
    source = Column(String(50))               # 기업명
    title = Column(String(255))               # 글 제목
    url = Column(Text)
    category = Column(String(50), nullable=True, index=True)
    
    published_at = Column(DateTime(timezone=True), index=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 분석 상태 및 결과
    is_analyzed = Column(Boolean, default=False, index=True)
    summary = Column(Text, nullable=True)
    field_id = Column(Integer, ForeignKey('FIELDS.field_id',ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)

class PostKeywordMapping(Base):
    __tablename__ = 'EXTERNAL_POSTS_KEYWORDS'
    keyword_id = Column(Integer, ForeignKey('KEYWORDS.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    post_id = Column(String(64), ForeignKey('EXTERNAL_POSTS.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
