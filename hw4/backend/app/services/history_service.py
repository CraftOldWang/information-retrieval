import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.history import SearchHistory, Snapshot
from app.schemas.history import SearchHistoryResponse
from app.schemas.search import SearchQuery

logger = logging.getLogger(__name__)

class HistoryService:
    """历史记录服务类，使用单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HistoryService, cls).__new__(cls)
        return cls._instance
    
    async def add_search_history(self, db: Session, user_id: int, query: SearchQuery) -> SearchHistory:
        """添加搜索历史"""
        try:
            # 创建搜索历史记录
            filters = {}
            if query.domain_filter:
                filters["domain_filter"] = query.domain_filter
            if query.date_from:
                filters["date_from"] = query.date_from.isoformat()
            if query.date_to:
                filters["date_to"] = query.date_to.isoformat()
            if query.file_type:
                filters["file_type"] = query.file_type
            
            history = SearchHistory(
                user_id=user_id,
                query=query.query,
                search_type=query.search_type,
                filters=filters,
                timestamp=datetime.utcnow()
            )
            db.add(history)
            db.commit()
            db.refresh(history)
            return history
        except Exception as e:
            db.rollback()
            logger.error(f"Add search history error: {e}")
            raise BadRequestException(f"Add search history error: {str(e)}")
    
    async def get_search_history(self, db: Session, user_id: int, page: int = 1, page_size: int = 10) -> SearchHistoryResponse:
        """获取搜索历史"""
        try:
            # 查询总数
            total = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).count()
            
            # 分页查询
            history_items = db.query(SearchHistory).filter(
                SearchHistory.user_id == user_id
            ).order_by(
                desc(SearchHistory.timestamp)
            ).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size
            
            return SearchHistoryResponse(
                items=history_items,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                total_results=total
            )
        except Exception as e:
            logger.error(f"Get search history error: {e}")
            raise BadRequestException(f"Get search history error: {str(e)}")
    
    async def delete_search_history(self, db: Session, user_id: int, history_id: int) -> bool:
        """删除搜索历史"""
        try:
            # 查询历史记录
            history = db.query(SearchHistory).filter(
                SearchHistory.id == history_id,
                SearchHistory.user_id == user_id
            ).first()
            
            if not history:
                raise NotFoundException("History not found")
            
            # 删除历史记录
            db.delete(history)
            db.commit()
            return True
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Delete search history error: {e}")
            raise BadRequestException(f"Delete search history error: {str(e)}")
    
    async def clear_search_history(self, db: Session, user_id: int) -> bool:
        """清空搜索历史"""
        try:
            # 删除所有历史记录
            db.query(SearchHistory).filter(SearchHistory.user_id == user_id).delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Clear search history error: {e}")
            raise BadRequestException(f"Clear search history error: {str(e)}")

class SnapshotService:
    """快照服务类，使用单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SnapshotService, cls).__new__(cls)
        return cls._instance
    
    async def get_snapshot(self, db: Session, url_id: str, timestamp: Optional[datetime] = None) -> Snapshot:
        """获取网页快照"""
        try:
            query = db.query(Snapshot).filter(Snapshot.url_id == url_id)
            
            if timestamp:
                # 查找最接近指定时间的快照
                snapshot = query.order_by(
                    abs(Snapshot.timestamp - timestamp).asc()
                ).first()
            else:
                # 查找最新的快照
                snapshot = query.order_by(desc(Snapshot.timestamp)).first()
            
            if not snapshot:
                raise NotFoundException("Snapshot not found")
            
            return snapshot
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Get snapshot error: {e}")
            raise BadRequestException(f"Get snapshot error: {str(e)}")
    
    async def add_snapshot(self, db: Session, url_id: str, url: str, title: str, html_content: str) -> Snapshot:
        """添加网页快照"""
        try:
            # 创建快照
            snapshot = Snapshot(
                url_id=url_id,
                url=url,
                title=title,
                html_content=html_content,
                timestamp=datetime.utcnow()
            )
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            return snapshot
        except Exception as e:
            db.rollback()
            logger.error(f"Add snapshot error: {e}")
            raise BadRequestException(f"Add snapshot error: {str(e)}")