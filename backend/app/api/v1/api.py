# 路由聚合模块
from fastapi import APIRouter

from app.api.v1.endpoints import (
    search,
    documents,
    users,
    snapshots,
    history,
    recommendations,
)

# 创建主API路由器
api_router = APIRouter()

# 注册子路由器
api_router.include_router(search.router, prefix="/search", tags=["搜索"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(snapshots.router, prefix="/snapshots", tags=["网页快照"])
api_router.include_router(history.router, prefix="/history", tags=["历史记录"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["推荐"]
)
