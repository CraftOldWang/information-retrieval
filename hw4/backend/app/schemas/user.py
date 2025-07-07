from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseResponse, PaginatedResponse

class UserBase(BaseModel):
    """用户基础模型"""
    username: str

class UserCreate(UserBase):
    """用户创建模型"""
    password: str

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str

class UserProfile(UserBase):
    """用户资料模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    user_id: int
    preferred_domains: Optional[List[str]] = None
    excluded_domains: Optional[List[str]] = None
    preferred_topics: Optional[List[str]] = None
    search_history_enabled: bool = True
    personalized_search_enabled: bool = True

    class Config:
        from_attributes = True

class UserFeedback(BaseModel):
    """用户反馈模型"""
    user_id: int
    document_id: str
    feedback_type: str  # click, bookmark, like, dislike
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

class UserFeedbackCreate(BaseModel):
    """用户反馈创建模型"""
    document_id: str
    feedback_type: str

class TokenResponse(BaseResponse):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class UserResponse(BaseResponse):
    """用户响应模型"""
    user: UserProfile

class UserPreferencesResponse(BaseResponse):
    """用户偏好设置响应模型"""
    preferences: UserPreferences