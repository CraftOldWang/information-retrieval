from fastapi import APIRouter

from app.api.v1 import search, users, history, snapshots

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(snapshots.router, prefix="/snapshots", tags=["snapshots"])