from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)  # 사용자 이름 추가
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    priority = Column(Integer, default=0)
    start_time = Column(DateTime)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow) 