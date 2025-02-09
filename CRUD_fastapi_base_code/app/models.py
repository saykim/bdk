from sqlalchemy import Column, Integer, String, Text, DateTime, Index, text, Enum
from sqlalchemy.sql import func
from .database import Base
import enum
from datetime import datetime

class ProcessStatus(str, enum.Enum):
    PENDING = "대기"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    ISSUE = "문제발생"

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 추가 필드
    category = Column(String(50), nullable=False, server_default="일반")
    product_name = Column(String(100), nullable=True)
    process_step = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, server_default=ProcessStatus.PENDING.value)
    attachment_path = Column(String(500), nullable=True)

    # 검색을 위한 인덱스 추가
    __table_args__ = (
        Index('idx_title_content', 'title', 'content'),
        Index('idx_author', 'author'),
    ) 