from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_user
from app.models.user import User, UserPreferences, UserFeedback
from app.schemas.user import (
    UserCreate, UserLogin, UserProfile, UserPreferences as UserPreferencesSchema,
    UserFeedbackCreate, TokenResponse, UserResponse, UserPreferencesResponse
)
from app.services.user_service import UserService

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """注册新用户"""
    user_service = UserService()
    user = await user_service.create_user(db, user_create)
    
    # 创建访问令牌
    access_token = user_service.create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserProfile(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user_service = UserService()
    user = await user_service.authenticate_user(db, user_login.username, user_login.password)
    
    # 创建访问令牌
    access_token = user_service.create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserProfile(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户资料"""
    return UserResponse(
        user=UserProfile(
            id=current_user.id,
            username=current_user.username,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )
    )

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户偏好设置"""
    user_service = UserService()
    preferences = await user_service.get_user_preferences(db, current_user.id)
    
    return UserPreferencesResponse(
        preferences=UserPreferencesSchema(
            user_id=preferences.user_id,
            preferred_domains=preferences.preferred_domains,
            excluded_domains=preferences.excluded_domains,
            preferred_topics=preferences.preferred_topics,
            search_history_enabled=preferences.search_history_enabled,
            personalized_search_enabled=preferences.personalized_search_enabled
        )
    )

@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户偏好设置"""
    user_service = UserService()
    preferences = await user_service.update_user_preferences(db, current_user.id, preferences_data)
    
    return UserPreferencesResponse(
        preferences=UserPreferencesSchema(
            user_id=preferences.user_id,
            preferred_domains=preferences.preferred_domains,
            excluded_domains=preferences.excluded_domains,
            preferred_topics=preferences.preferred_topics,
            search_history_enabled=preferences.search_history_enabled,
            personalized_search_enabled=preferences.personalized_search_enabled
        )
    )

@router.post("/feedback", response_model=dict)
async def submit_feedback(
    feedback: UserFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交搜索结果反馈"""
    user_service = UserService()
    await user_service.add_user_feedback(
        db, current_user.id, feedback.document_id, feedback.feedback_type
    )
    
    return {"message": "Feedback submitted successfully"}