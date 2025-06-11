# 搜索历史模块
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, Any
import logging

from app.core.config import settings
from app.services.user_service import get_current_user
from app.services.history_service import HistoryService
from app.models.schemas import UserProfile, SearchHistoryResponse

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取历史服务实例
history_service = HistoryService()


@router.get("/", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: UserProfile = Depends(get_current_user),
) -> SearchHistoryResponse:
    """
    获取当前用户的搜索历史。

    - **page**: 页码 (从1开始)
    - **page_size**: 每页结果数
    """
    try:
        history = await history_service.get_user_history(
            current_user.id, page, page_size
        )
        return history
    except Exception as e:
        logger.error(f"获取搜索历史出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"历史服务错误: {str(e)}")


@router.delete("/{history_id}", response_model=Dict[str, Any])
async def delete_history_item(
    history_id: int = Path(..., description="历史记录ID"),
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    删除单条搜索历史记录。

    - **history_id**: 历史记录ID
    """
    try:
        success = await history_service.delete_history_item(history_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"历史记录不存在或无权删除: {history_id}"
            )

        return {"success": True, "message": f"成功删除历史记录 {history_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史记录出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"历史服务错误: {str(e)}")


@router.delete("/", response_model=Dict[str, Any])
async def clear_search_history(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    清空当前用户的所有搜索历史。
    """
    try:
        count = await history_service.clear_user_history(current_user.id)
        return {"success": True, "message": f"成功清空搜索历史，共删除 {count} 条记录"}
    except Exception as e:
        logger.error(f"清空搜索历史出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"历史服务错误: {str(e)}")
