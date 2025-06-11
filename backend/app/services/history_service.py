# 搜索历史服务模块
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional
import json

from app.core.config import settings
from app.models.schemas import SearchHistoryResponse, SearchHistoryItem, SearchHistoryCreate

logger = logging.getLogger(__name__)


class HistoryService:
    """搜索历史服务类"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DATABASE_URL
        self._init_database()
    
    def _init_database(self):
        """初始化搜索历史数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建搜索历史表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        query TEXT NOT NULL,
                        search_type VARCHAR(50) DEFAULT 'normal',
                        results_count INTEGER DEFAULT 0,
                        filters TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引提高查询性能
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_search_history_user_id 
                    ON search_history(user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_search_history_created_at 
                    ON search_history(created_at)
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"初始化搜索历史数据库失败: {str(e)}", exc_info=True)
            raise
    
    async def add_search_history(self, user_id: Optional[int], history_data: SearchHistoryCreate, 
                               filters: Optional[dict] = None) -> int:
        """添加搜索历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO search_history (user_id, query, search_type, results_count, filters)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    history_data.query,
                    history_data.search_type,
                    history_data.results_count,
                    json.dumps(filters) if filters else None
                ))
                
                history_id = cursor.lastrowid
                conn.commit()
                return history_id
                
        except Exception as e:
            logger.error(f"添加搜索历史失败: {str(e)}", exc_info=True)
            raise
    
    async def get_user_history(self, user_id: int, page: int = 1, page_size: int = 10) -> SearchHistoryResponse:
        """获取用户搜索历史"""
        try:
            offset = (page - 1) * page_size
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取总数
                cursor.execute("""
                    SELECT COUNT(*) FROM search_history WHERE user_id = ?
                """, (user_id,))
                total = cursor.fetchone()[0]
                
                # 获取历史记录
                cursor.execute("""
                    SELECT id, query, search_type, results_count, created_at
                    FROM search_history 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, page_size, offset))
                
                rows = cursor.fetchall()
                
                items = []
                for row in rows:
                    items.append(SearchHistoryItem(
                        id=row[0],
                        query=row[1],
                        search_type=row[2],
                        results_count=row[3],
                        created_at=datetime.fromisoformat(row[4])
                    ))
                
                return SearchHistoryResponse(
                    items=items,
                    total=total
                )
                
        except Exception as e:
            logger.error(f"获取用户搜索历史失败: {str(e)}", exc_info=True)
            raise
    
    async def get_anonymous_history(self, session_id: str, page: int = 1, page_size: int = 10) -> SearchHistoryResponse:
        """获取匿名用户搜索历史（基于会话）"""
        try:
            # 对于匿名用户，我们可以使用Redis或临时存储
            # 这里暂时返回空历史
            return SearchHistoryResponse(items=[], total=0)
            
        except Exception as e:
            logger.error(f"获取匿名用户搜索历史失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_history_item(self, history_id: int, user_id: int) -> bool:
        """删除单条历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM search_history 
                    WHERE id = ? AND user_id = ?
                """, (history_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"删除搜索历史失败: {str(e)}", exc_info=True)
            return False
    
    async def clear_user_history(self, user_id: int) -> int:
        """清空用户所有搜索历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM search_history WHERE user_id = ?
                """, (user_id,))
                
                count = cursor.rowcount
                conn.commit()
                return count
                
        except Exception as e:
            logger.error(f"清空用户搜索历史失败: {str(e)}", exc_info=True)
            return 0
    
    async def get_popular_queries(self, limit: int = 10, days: int = 7) -> List[dict]:
        """获取热门搜索查询"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM search_history 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY query
                    ORDER BY count DESC
                    LIMIT ?
                """.format(days), (limit,))
                
                rows = cursor.fetchall()
                return [{"query": row[0], "count": row[1]} for row in rows]
                
        except Exception as e:
            logger.error(f"获取热门查询失败: {str(e)}", exc_info=True)
            return []
    
    async def get_user_query_patterns(self, user_id: int, limit: int = 20) -> List[str]:
        """获取用户查询模式，用于个性化推荐"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM search_history 
                    WHERE user_id = ?
                    GROUP BY query
                    ORDER BY count DESC, created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                return [row[0] for row in rows]
                
        except Exception as e:
            logger.error(f"获取用户查询模式失败: {str(e)}", exc_info=True)
            return []
