from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseResponse

class SearchQuery(BaseModel):
    """搜索查询模型"""
    query: str
    page: int = 1
    page_size: int = 10
    search_type: Optional[str] = None  # normal, phrase, wildcard
    domain_filter: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    file_type: Optional[List[str]] = None
    user_id: Optional[int] = None

class DocumentSearchQuery(BaseModel):
    """文档搜索查询模型"""
    query: str
    page: int = 1
    page_size: int = 10
    doc_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_type: Optional[str] = None  # normal, phrase, wildcard
    user_id: Optional[int] = None

class SearchResultHighlight(BaseModel):
    """搜索结果高亮模型"""
    title: Optional[List[str]] = None
    content: Optional[List[str]] = None

class SearchResultItem(BaseModel):
    """搜索结果项模型"""
    id: str
    url: str
    title: str
    snippet: Optional[str] = None
    content: Optional[str] = None
    domain: Optional[str] = None
    date: Optional[datetime] = None
    highlights: Optional[SearchResultHighlight] = None
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentResultItem(BaseModel):
    """文档搜索结果项模型"""
    id: str
    url: str
    title: str
    filename: str
    type: str
    snippet: Optional[str] = None
    author: Optional[str] = None
    upload_date: Optional[datetime] = None
    file_size: Optional[int] = None
    highlights: Optional[SearchResultHighlight] = None
    score: Optional[float] = None

class SearchResponse(BaseResponse):
    """搜索响应模型"""
    results: List[SearchResultItem]
    page: int
    page_size: int
    total_pages: int
    total_results: int
    query: str
    search_time: float
    related_queries: Optional[List[str]] = None

class DocumentSearchResponse(BaseResponse):
    """文档搜索响应模型"""
    results: List[DocumentResultItem]
    page: int
    page_size: int
    total_pages: int
    total_results: int
    query: str
    search_time: float

class SuggestionResponse(BaseResponse):
    """搜索建议响应模型"""
    suggestions: List[str]

class RecommendationResponse(BaseResponse):
    """搜索推荐响应模型"""
    recommendations: List[str]