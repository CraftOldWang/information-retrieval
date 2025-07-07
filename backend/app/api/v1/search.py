from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_user, get_optional_current_user
from app.models.user import User, UserPreferences
from app.schemas.search import (
    SearchQuery, DocumentSearchQuery, SearchResponse, DocumentSearchResponse,
    SuggestionResponse, RecommendationResponse
)
from app.services.elasticsearch_service import ElasticsearchService
from app.services.history_service import HistoryService
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="搜索查询"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.SEARCH_DEFAULT_PAGE_SIZE, ge=1, le=settings.SEARCH_MAX_PAGE_SIZE, description="每页结果数"),
    search_type: Optional[str] = Query(None, description="搜索类型: normal, phrase, wildcard"),
    file_type: Optional[List[str]] = Query(None, description="文件类型")
):
    """执行搜索"""
    # 创建搜索查询对象
    query = SearchQuery(
        query=q,
        page=page,
        page_size=page_size,
        search_type=search_type,
        file_type=file_type,
        user_id=None
    )
    
    # 执行搜索
    search_service = ElasticsearchService()
    response = await search_service.search(query)
    
    return response

@router.get("/personalized", response_model=SearchResponse)
async def personalized_search(
    q: str = Query(..., description="搜索查询"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.SEARCH_DEFAULT_PAGE_SIZE, ge=1, le=settings.SEARCH_MAX_PAGE_SIZE, description="每页结果数"),
    search_type: Optional[str] = Query(None, description="搜索类型: normal, phrase, wildcard"),
    file_type: Optional[List[str]] = Query(None, description="文件类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行个性化搜索"""
    # 获取用户偏好设置
    preferences = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    
    # 如果用户禁用了个性化搜索，则执行普通搜索
    if not preferences or not preferences.personalized_search_enabled:
        return await search(q, page, page_size, search_type, file_type)
    
    # 创建搜索查询对象，并添加用户偏好
    query = SearchQuery(
        query=q,
        page=page,
        page_size=page_size,
        search_type=search_type,
        file_type=file_type,
        user_id=current_user.id
    )
    
    # 执行搜索
    search_service = ElasticsearchService()
    response = await search_service.search(query)
    
    # 记录搜索历史
    history_service = HistoryService()
    await history_service.add_search_history(db, current_user.id, query)
    
    return response

@router.get("/documents", response_model=DocumentSearchResponse)
async def search_documents(
    q: str = Query(..., description="搜索查询"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.SEARCH_DEFAULT_PAGE_SIZE, ge=1, le=settings.SEARCH_MAX_PAGE_SIZE, description="每页结果数"),
    doc_type: Optional[List[str]] = Query(None, description="文档类型"),
    search_type: Optional[str] = Query(None, description="搜索类型: normal, phrase, wildcard"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """执行文档搜索"""
    # 创建文档搜索查询对象
    query = DocumentSearchQuery(
        query=q,
        page=page,
        page_size=page_size,
        doc_types=doc_type,
        search_type=search_type,
        user_id=current_user.id if current_user else None
    )
    
    # 执行搜索
    search_service = ElasticsearchService()
    response = await search_service.search_documents(query)
    
    # 如果用户已登录，记录搜索历史
    if current_user:
        history_service = HistoryService()
        await history_service.add_search_history(db, current_user.id, SearchQuery(
            query=q,
            page=page,
            page_size=page_size,
            search_type="document",
            file_type=doc_type,
            user_id=current_user.id
        ))
    
    return response

@router.get("/suggest", response_model=SuggestionResponse)
async def get_suggestions(
    q: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(settings.SEARCH_SUGGESTION_LIMIT, ge=1, le=20, description="建议数量")
):
    """获取搜索建议"""
    search_service = ElasticsearchService()
    suggestions = await search_service.get_suggestions(q, limit)
    
    return SuggestionResponse(suggestions=suggestions)

@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    q: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(5, ge=1, le=10, description="推荐数量")
):
    """获取搜索推荐"""
    search_service = ElasticsearchService()
    recommendations = await search_service.get_recommendations(q, limit)
    
    return RecommendationResponse(recommendations=recommendations)

@router.get("/recommendations/related", response_model=RecommendationResponse)
async def get_related_recommendations(
    q: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(5, ge=1, le=10, description="推荐数量")
):
    """获取相关搜索推荐"""
    search_service = ElasticsearchService()
    recommendations = await search_service.get_recommendations(q, limit)
    
    return RecommendationResponse(recommendations=recommendations)