from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class SearchHistory(Base):
    """搜索历史模型"""
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    query = Column(String(200), nullable=False)
    search_type = Column(String(20), nullable=True)  # normal, phrase, wildcard
    filters = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="search_history")

class Snapshot(Base):
    """网页快照模型"""
    url_id = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)
    html_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)