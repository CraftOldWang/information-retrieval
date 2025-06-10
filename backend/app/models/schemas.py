# 数据模型定义
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = True
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """错误响应模型"""

    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 搜索相关模型
class SearchQuery(BaseModel):
    """搜索查询模型"""

    query: str = Field(..., min_length=1, max_length=500, description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    search_type: str = Field(
        default="normal", description="搜索类型：normal, phrase, wildcard, document"
    )
    domain_filter: Optional[List[str]] = Field(default=None, description="域名过滤")
    date_from: Optional[datetime] = Field(default=None, description="开始日期")
    date_to: Optional[datetime] = Field(default=None, description="结束日期")


class SearchResult(BaseModel):
    """搜索结果项模型"""

    id: str = Field(..., description="文档ID")
    url: HttpUrl = Field(..., description="页面URL")
    title: str = Field(..., description="页面标题")
    snippet: str = Field(..., description="内容摘要")
    domain: str = Field(..., description="域名")
    score: float = Field(..., description="相关性得分")
    highlight: Optional[Dict[str, List[str]]] = Field(
        default=None, description="高亮内容"
    )
    crawl_time: datetime = Field(..., description="爬取时间")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="附件信息"
    )


class SearchResponse(BaseResponse):
    """搜索响应模型"""

    total: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    results: List[SearchResult] = Field(..., description="搜索结果列表")
    aggregations: Optional[Dict[str, Any]] = Field(default=None, description="聚合信息")
    suggestions: Optional[List[str]] = Field(default=None, description="搜索建议")


# 用户相关模型
class UserCreate(BaseModel):
    """用户创建模型"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    college: Optional[str] = Field(default=None, max_length=100, description="学院")
    major: Optional[str] = Field(default=None, max_length=100, description="专业")
    grade: Optional[str] = Field(default=None, max_length=20, description="年级")


class UserLogin(BaseModel):
    """用户登录模型"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserProfile(BaseModel):
    """用户资料模型"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    college: Optional[str] = Field(default=None, description="学院")
    major: Optional[str] = Field(default=None, description="专业")
    grade: Optional[str] = Field(default=None, description="年级")
    created_at: datetime = Field(..., description="注册时间")
    is_active: bool = Field(default=True, description="是否激活")


class Token(BaseModel):
    """访问令牌模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserProfile = Field(..., description="用户信息")


# 搜索历史模型
class SearchHistoryCreate(BaseModel):
    """搜索历史创建模型"""

    query: str = Field(..., description="搜索查询")
    search_type: str = Field(default="normal", description="搜索类型")
    results_count: int = Field(default=0, description="结果数量")


class SearchHistoryItem(BaseModel):
    """搜索历史项模型"""

    id: int = Field(..., description="历史记录ID")
    query: str = Field(..., description="搜索查询")
    search_type: str = Field(..., description="搜索类型")
    results_count: int = Field(..., description="结果数量")
    created_at: datetime = Field(..., description="搜索时间")


class SearchHistoryResponse(BaseResponse):
    """搜索历史响应模型"""

    items: List[SearchHistoryItem] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总记录数")


# 用户偏好模型
class UserPreferences(BaseModel):
    """用户偏好模型"""

    domain_preferences: Optional[Dict[str, float]] = Field(
        default=None, description="域名偏好"
    )
    topic_preferences: Optional[Dict[str, float]] = Field(
        default=None, description="主题偏好"
    )
    search_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="搜索过滤器偏好"
    )


# 推荐模型
class RecommendationItem(BaseModel):
    """推荐项模型"""

    type: str = Field(..., description="推荐类型：query, content")
    content: str = Field(..., description="推荐内容")
    score: float = Field(..., description="推荐得分")
    reason: Optional[str] = Field(default=None, description="推荐原因")


class RecommendationResponse(BaseResponse):
    """推荐响应模型"""

    recommendations: List[RecommendationItem] = Field(..., description="推荐列表")


# 统计模型
class SearchStatistics(BaseModel):
    """搜索统计模型"""

    total_searches: int = Field(..., description="总搜索次数")
    unique_queries: int = Field(..., description="唯一查询数")
    avg_results_per_query: float = Field(..., description="平均每查询结果数")
    popular_queries: List[Dict[str, Any]] = Field(..., description="热门查询")
    search_trends: List[Dict[str, Any]] = Field(..., description="搜索趋势")
