from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.dependencies.database import Base


class Posts(Base):
    __tablename__ = "POSTS"
    url = Column(String, nullable=False, primary_key=True)  # unique=True는 불필요
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("USER.user_id"),
        nullable=False,
        primary_key=True,
    )
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("PLATFORM.platform_id"),
        nullable=False,
        primary_key=True,
    )
    date = Column(DateTime, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)


class POST_AGG(Base):
    __tablename__ = "POST_AGG"
    category = Column(String, nullable=False, primary_key=True)
    date = Column(DateTime, nullable=False, primary_key=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("USER.user_id"),
        nullable=False,
        primary_key=True,
    )
    count = Column(Integer, nullable=False)


class POST_KEYWORD(Base):
    __tablename__ = "POST_KEYWORDS"

    url = Column(String, nullable=False, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    platform_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    keyword_id = Column(
        Integer,
        ForeignKey("KEYWORDS.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["url", "user_id", "platform_id"],
            ["POSTS.url", "POSTS.user_id", "POSTS.platform_id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )