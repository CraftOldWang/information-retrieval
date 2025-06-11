# 用户服务模块
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
import logging

from app.core.config import settings
from app.services.user_service import UserService, create_access_token, get_current_user
from app.models.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserProfile,
    UserPreferences,
)

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取用户服务实例
user_service = UserService()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate = Body(...)) -> Token:
    """
    注册新用户，成功后返回访问令牌。

    - **username**: 用户名，3-50个字符
    - **email**: 电子邮件地址
    - **password**: 密码，6-128个字符
    - **college**: (可选) 学院
    - **major**: (可选) 专业
    - **grade**: (可选) 年级
    """
    try:
        # 尝试创建用户
        user = await user_service.create_user(user_data)

        # 创建访问令牌
        access_token = create_access_token(data={"sub": user.username})

        # 返回令牌和用户信息
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户注册出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户服务错误: {str(e)}")


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin = Body(...)) -> Token:
    """
    用户登录，成功后返回访问令牌。

    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    try:
        # 验证用户凭据
        user = await user_service.authenticate_user(
            user_data.username, user_data.password
        )
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 创建访问令牌
        access_token = create_access_token(data={"sub": user.username})

        # 返回令牌和用户信息
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户服务错误: {str(e)}")


@router.get("/me", response_model=UserProfile)
async def get_user_profile(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """
    获取当前登录用户的个人资料。
    """
    return current_user


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: UserProfile = Depends(get_current_user),
) -> UserPreferences:
    """
    获取当前登录用户的偏好设置。
    """
    try:
        preferences = await user_service.get_user_preferences(current_user.id)
        return preferences
    except Exception as e:
        logger.error(f"获取用户偏好出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户服务错误: {str(e)}")


@router.post("/preferences", response_model=Dict[str, Any])
async def update_user_preferences(
    preferences: UserPreferences = Body(...),
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    更新当前登录用户的偏好设置。

    - **domain_preferences**: (可选) 域名偏好
    - **topic_preferences**: (可选) 主题偏好
    - **search_filters**: (可选) 搜索过滤器偏好
    """
    try:
        success = await user_service.update_user_preferences(
            current_user.id, preferences
        )
        return {"success": success, "message": "用户偏好设置已更新"}
    except Exception as e:
        logger.error(f"更新用户偏好出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户服务错误: {str(e)}")


@router.post("/feedback", response_model=Dict[str, Any])
async def submit_feedback(
    query_id: str = Body(..., embed=True),
    url: str = Body(..., embed=True),
    action: str = Body(..., embed=True),
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    提交搜索结果反馈。

    - **query_id**: 查询ID
    - **url**: 反馈的URL
    - **action**: 反馈动作，如 "click", "bookmark", "dislike" 等
    """
    try:
        await user_service.record_feedback(current_user.id, query_id, url, action)
        return {"success": True, "message": "反馈已记录"}
    except Exception as e:
        logger.error(f"记录用户反馈出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户服务错误: {str(e)}")
