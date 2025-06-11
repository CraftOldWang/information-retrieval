# 搜索服务模块
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.config import settings
# 修改导入路径，使用新的实现
from app.services.elasticsearch_service_implementation import ElasticsearchService
from app.models.schemas import SearchQuery, SearchResponse
from app.services.user_service import get_current_user, get_optional_user
from app.models.schemas import UserProfile

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取Elasticsearch服务实例
es_service = ElasticsearchService()


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页结果数"),
    search_type: str = Query(
        "normal", description="搜索类型：normal, phrase, wildcard"
    ),
    domain: Optional[List[str]] = Query(None, description="域名过滤"),
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> SearchResponse:
    """
    基础搜索API，支持关键词搜索、分页、域名过滤等功能。

    - **q**: 搜索关键词
    - **page**: 页码 (从1开始)
    - **page_size**: 每页结果数
    - **search_type**: 搜索类型 (normal: 普通搜索, phrase: 短语搜索, wildcard: 通配符搜索)
    - **domain**: 域名过滤列表
    - **date_from**: 开始日期过滤
    - **date_to**: 结束日期过滤
    """
    try:
        # 构建搜索查询
        query = SearchQuery(
            query=q,
            page=page,
            page_size=page_size,
            search_type=search_type,
            domain_filter=domain,
            date_from=date_from,
            date_to=date_to,
        )

        # 执行搜索
        results = await es_service.search(query, current_user)

        # 如果用户已登录，记录搜索历史
        if current_user:
            await es_service.record_search_history(
                current_user.id, query, results.total
            )

        return results
    except Exception as e:
        logger.error(f"搜索出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.get("/suggest", response_model=Dict[str, Any])
async def search_suggestions(
    q: str = Query(..., min_length=1, description="输入的查询词"),
    limit: int = Query(10, ge=1, le=50, description="返回建议数量"),
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    搜索建议API，提供自动补全功能。

    - **q**: 已输入的查询词
    - **limit**: 返回的建议数量
    """
    try:
        suggestions = await es_service.get_suggestions(q, limit, current_user)
        return {
            "success": True,
            "query": q,
            "suggestions": suggestions,
        }
    except Exception as e:
        logger.error(f"获取搜索建议出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索建议服务错误: {str(e)}")


@router.get("/personalized", response_model=SearchResponse)
async def personalized_search(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页结果数"),
    current_user: UserProfile = Depends(get_current_user),
) -> SearchResponse:
    """
    个性化搜索API，根据用户历史行为和偏好提供定制化结果。

    - **q**: 搜索关键词
    - **page**: 页码 (从1开始)
    - **page_size**: 每页结果数
    """
    try:
        # 构建搜索查询
        query = SearchQuery(
            query=q,
            page=page,
            page_size=page_size,
        )

        # 执行个性化搜索
        results = await es_service.personalized_search(query, current_user)

        # 记录搜索历史
        await es_service.record_search_history(current_user.id, query, results.total)

        return results
    except Exception as e:
        logger.error(f"个性化搜索出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"个性化搜索服务错误: {str(e)}")
