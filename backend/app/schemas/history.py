from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseResponse, PaginatedResponse

class SearchHistory(BaseModel):
    """搜索历史模型"""
    id: int
    user_id: int
    query: str
    search_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

class SearchHistoryResponse(PaginatedResponse[SearchHistory]):
    """搜索历史响应模型"""
    pass

class SnapshotQuery(BaseModel):
    """快照查询模型"""
    url_id: str
    timestamp: Optional[datetime] = None

class Snapshot(BaseModel):
    """网页快照模型"""
    id: int
    url_id: str
    url: str
    title: str
    html_content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class SnapshotResponse(BaseResponse):
    """网页快照响应模型"""
    snapshot: Snapshot