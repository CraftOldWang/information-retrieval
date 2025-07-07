from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class User(Base):
    """用户模型"""
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 关系
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    feedbacks = relationship("UserFeedback", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")

class UserPreferences(Base):
    """用户偏好设置模型"""
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    preferred_domains = Column(JSON, nullable=True)
    excluded_domains = Column(JSON, nullable=True)
    preferred_topics = Column(JSON, nullable=True)
    search_history_enabled = Column(Boolean, default=True)
    personalized_search_enabled = Column(Boolean, default=True)
    
    # 关系
    user = relationship("User", back_populates="preferences")

class UserFeedback(Base):
    """用户反馈模型"""
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    document_id = Column(String(100), nullable=False)
    feedback_type = Column(String(20), nullable=False)  # click, bookmark, like, dislike
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="feedbacks")