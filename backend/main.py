# NKU搜索引擎后端服务
# FastAPI应用入口文件

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from typing import Dict, Any
import os

# 导入路由模块
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="南开大学搜索引擎API",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "内部服务器错误", "status_code": 500},
    )


# 健康检查
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    return {
        "status": "ok",
        "message": "NKU搜索引擎后端服务运行正常",
        "version": settings.VERSION,
    }


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("NKU搜索引擎后端服务启动中...")

    # 这里可以添加数据库连接、缓存初始化等操作
    # await init_database()
    # await init_elasticsearch()
    # await init_redis()

    logger.info("NKU搜索引擎后端服务启动完成")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("NKU搜索引擎后端服务正在关闭...")

    # 这里可以添加资源清理操作
    # await close_database()
    # await close_elasticsearch()
    # await close_redis()

    logger.info("NKU搜索引擎后端服务已关闭")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
