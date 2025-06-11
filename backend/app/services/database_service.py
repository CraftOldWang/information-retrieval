# 数据库初始化服务
import os
import sqlite3
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DATABASE_URL
        self.ensure_data_directory()
        self.init_database()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"数据目录已准备: {db_dir}")
        except Exception as e:
            logger.error(f"创建数据目录失败: {str(e)}", exc_info=True)
            raise
    
    def init_database(self):
        """初始化所有数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 启用外键约束
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # 创建用户表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        college VARCHAR(100),
                        major VARCHAR(100),
                        grade VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # 创建用户偏好表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id INTEGER PRIMARY KEY,
                        domain_preferences TEXT,
                        topic_preferences TEXT,
                        search_filters TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建搜索历史表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        query TEXT NOT NULL,
                        search_type VARCHAR(50) DEFAULT 'normal',
                        results_count INTEGER DEFAULT 0,
                        filters TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                    )
                """)
                
                # 创建用户反馈表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        query_id VARCHAR(255),
                        url TEXT NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # 创建查询关联表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_associations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query1 TEXT NOT NULL,
                        query2 TEXT NOT NULL,
                        association_score REAL DEFAULT 1.0,
                        co_occurrence_count INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(query1, query2)
                    )
                """)
                
                # 创建热门查询缓存表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS popular_queries_cache (
                        query TEXT PRIMARY KEY,
                        count INTEGER NOT NULL,
                        rank_position INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建用户会话表（用于匿名用户）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id VARCHAR(255) PRIMARY KEY,
                        search_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引以提高查询性能
                self._create_indexes(cursor)
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
            raise
    
    def _create_indexes(self, cursor):
        """创建数据库索引"""
        indexes = [
            # 用户表索引
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            
            # 搜索历史索引
            "CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_type ON search_history(search_type)",
            
            # 用户反馈索引
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_url ON user_feedback(url)",
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_action ON user_feedback(action)",
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at)",
            
            # 查询关联索引
            "CREATE INDEX IF NOT EXISTS idx_query_associations_query1 ON query_associations(query1)",
            "CREATE INDEX IF NOT EXISTS idx_query_associations_query2 ON query_associations(query2)",
            "CREATE INDEX IF NOT EXISTS idx_query_associations_score ON query_associations(association_score)",
            
            # 热门查询索引
            "CREATE INDEX IF NOT EXISTS idx_popular_queries_count ON popular_queries_cache(count)",
            "CREATE INDEX IF NOT EXISTS idx_popular_queries_rank ON popular_queries_cache(rank_position)",
            "CREATE INDEX IF NOT EXISTS idx_popular_queries_updated ON popular_queries_cache(last_updated)",
            
            # 会话索引
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"创建索引失败: {index_sql}, 错误: {str(e)}")
    
    def get_database_stats(self) -> dict:
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 用户统计
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                stats['active_users'] = cursor.fetchone()[0]
                
                # 搜索历史统计
                cursor.execute("SELECT COUNT(*) FROM search_history")
                stats['total_searches'] = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT query) FROM search_history 
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                stats['unique_queries_week'] = cursor.fetchone()[0]
                
                # 反馈统计
                cursor.execute("SELECT COUNT(*) FROM user_feedback")
                stats['total_feedback'] = cursor.fetchone()[0]
                
                # 数据库大小
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"获取数据库统计失败: {str(e)}", exc_info=True)
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 清理过期会话
                cursor.execute("""
                    DELETE FROM user_sessions 
                    WHERE expires_at < datetime('now') OR last_activity < datetime('now', '-7 days')
                """)
                
                # 清理过期的热门查询缓存
                cursor.execute("""
                    DELETE FROM popular_queries_cache 
                    WHERE last_updated < datetime('now', '-24 hours')
                """)
                
                # 可选：清理很旧的搜索历史（保留用户自己的）
                if days > 0:
                    cursor.execute("""
                        DELETE FROM search_history 
                        WHERE user_id IS NULL AND created_at < datetime('now', '-{} days')
                    """.format(days))
                
                conn.commit()
                logger.info(f"数据清理完成，清理了{days}天前的匿名搜索记录")
                
        except Exception as e:
            logger.error(f"数据清理失败: {str(e)}", exc_info=True)


# 全局数据库服务实例
db_service = DatabaseService()
