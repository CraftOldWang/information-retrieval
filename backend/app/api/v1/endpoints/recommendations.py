# 推荐服务模块
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
import logging

from app.core.config import settings
from app.services.recommendation_service import RecommendationService
from app.services.user_service import get_current_user, get_optional_user
from app.models.schemas import UserProfile, RecommendationResponse

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取推荐服务实例
recommendation_service = RecommendationService()


@router.get("/queries", response_model=Dict[str, Any])
async def get_query_recommendations(
    q: str = Query("", description="当前输入的查询词"),
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    current_user: UserProfile = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    获取查询词推荐，用于搜索框自动完成和查询建议。

    - **q**: 已输入的查询词前缀
    - **limit**: 返回的推荐数量
    """
    try:
        recommendations = await recommendation_service.get_query_recommendations(
            q, limit, current_user
        )
        return {"success": True, "input": q, "recommendations": recommendations}
    except Exception as e:
        logger.error(f"获取查询推荐出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")


@router.get("/related", response_model=Dict[str, Any])
async def get_related_queries(
    q: str = Query(..., description="完整的查询词"),
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    current_user: UserProfile = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    获取相关查询，用于"相关搜索"功能。

    - **q**: 完整的查询词
    - **limit**: 返回的相关查询数量
    """
    try:
        related = await recommendation_service.get_related_queries(
            q, limit, current_user
        )
        return {"success": True, "query": q, "related_queries": related}
    except Exception as e:
        logger.error(f"获取相关查询出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")


@router.get("/popular", response_model=Dict[str, List[str]])
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: UserProfile = Depends(get_optional_user),
) -> Dict[str, List[str]]:
    """
    获取热门搜索查询。

    - **limit**: 返回的热门查询数量
    """
    try:
        popular = await recommendation_service.get_popular_queries(limit)
        return {"popular_queries": popular}
    except Exception as e:
        logger.error(f"获取热门查询出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")


@router.get("/personalized", response_model=RecommendationResponse)
async def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    current_user: UserProfile = Depends(get_current_user),
) -> RecommendationResponse:
    """
    获取个性化内容推荐，基于用户历史行为和偏好。

    - **limit**: 返回的推荐数量
    """
    try:
        recommendations = await recommendation_service.get_personalized_recommendations(
            current_user, limit
        )
        return recommendations
    except Exception as e:
        logger.error(f"获取个性化推荐出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")
