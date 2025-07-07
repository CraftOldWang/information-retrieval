from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.history import SearchHistoryResponse, SnapshotResponse
from app.services.history_service import HistoryService, SnapshotService
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.SEARCH_HISTORY_LIMIT, ge=1, le=100, description="每页结果数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取搜索历史"""
    history_service = HistoryService()
    return await history_service.get_search_history(db, current_user.id, page, page_size)

@router.delete("/{history_id}", response_model=dict)
async def delete_search_history(
    history_id: int = Path(..., description="历史记录ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除搜索历史"""
    history_service = HistoryService()
    await history_service.delete_search_history(db, current_user.id, history_id)
    return {"message": "History deleted successfully"}

@router.delete("/all", response_model=dict)
async def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空搜索历史"""
    history_service = HistoryService()
    await history_service.clear_search_history(db, current_user.id)
    return {"message": "All history cleared successfully"}