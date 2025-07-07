from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel):
    """基础响应模型"""
    code: str = "success"
    message: str = "Success"

class ErrorResponse(BaseResponse):
    """错误响应模型"""
    code: str = "error"
    message: str
    detail: Optional[str] = None

class PaginatedResponse(BaseResponse, Generic[T]):
    """分页响应模型"""
    items: List[T]
    page: int
    page_size: int
    total_pages: int
    total_results: int