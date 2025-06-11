# 用户服务模块
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.schemas import UserCreate, UserProfile, UserPreferences

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT认证
security = HTTPBearer()


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DATABASE_URL
        self._init_database()
    
    def _init_database(self):
        """初始化用户数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
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
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"初始化用户数据库失败: {str(e)}", exc_info=True)
            raise
    
    async def create_user(self, user_data: UserCreate) -> UserProfile:
        """创建新用户"""
        try:
            # 检查用户名和邮箱是否已存在
            if await self._user_exists(user_data.username, user_data.email):
                raise ValueError("用户名或邮箱已存在")
            
            # 加密密码
            password_hash = pwd_context.hash(user_data.password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, college, major, grade)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_data.username,
                    user_data.email,
                    password_hash,
                    user_data.college,
                    user_data.major,
                    user_data.grade
                ))
                
                user_id = cursor.lastrowid
                conn.commit()
            
            # 返回用户信息
            return await self.get_user_by_id(user_id)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}", exc_info=True)
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserProfile]:
        """验证用户凭据"""
        try:
            user = await self.get_user_by_username_or_email(username)
            if not user:
                return None
            
            # 验证密码
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,))
                result = cursor.fetchone()
                
                if result and pwd_context.verify(password, result[0]):
                    return user
            
            return None
            
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}", exc_info=True)
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """根据ID获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, college, major, grade, created_at, is_active
                    FROM users WHERE id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    return UserProfile(
                        id=result[0],
                        username=result[1],
                        email=result[2],
                        college=result[3],
                        major=result[4],
                        grade=result[5],
                        created_at=datetime.fromisoformat(result[6]),
                        is_active=bool(result[7])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}", exc_info=True)
            return None
    
    async def get_user_by_username_or_email(self, username_or_email: str) -> Optional[UserProfile]:
        """根据用户名或邮箱获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, college, major, grade, created_at, is_active
                    FROM users WHERE username = ? OR email = ?
                """, (username_or_email, username_or_email))
                
                result = cursor.fetchone()
                if result:
                    return UserProfile(
                        id=result[0],
                        username=result[1],
                        email=result[2],
                        college=result[3],
                        major=result[4],
                        grade=result[5],
                        created_at=datetime.fromisoformat(result[6]),
                        is_active=bool(result[7])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}", exc_info=True)
            return None
    
    async def get_user_preferences(self, user_id: int) -> UserPreferences:
        """获取用户偏好"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT domain_preferences, topic_preferences, search_filters
                    FROM user_preferences WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    import json
                    return UserPreferences(
                        domain_preferences=json.loads(result[0]) if result[0] else None,
                        topic_preferences=json.loads(result[1]) if result[1] else None,
                        search_filters=json.loads(result[2]) if result[2] else None
                    )
                else:
                    # 返回默认偏好
                    return UserPreferences()
            
        except Exception as e:
            logger.error(f"获取用户偏好失败: {str(e)}", exc_info=True)
            return UserPreferences()
    
    async def update_user_preferences(self, user_id: int, preferences: UserPreferences) -> bool:
        """更新用户偏好"""
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在记录
                cursor.execute("SELECT user_id FROM user_preferences WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("""
                        UPDATE user_preferences 
                        SET domain_preferences = ?, topic_preferences = ?, search_filters = ?, updated_at = ?
                        WHERE user_id = ?
                    """, (
                        json.dumps(preferences.domain_preferences) if preferences.domain_preferences else None,
                        json.dumps(preferences.topic_preferences) if preferences.topic_preferences else None,
                        json.dumps(preferences.search_filters) if preferences.search_filters else None,
                        datetime.now(),
                        user_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO user_preferences (user_id, domain_preferences, topic_preferences, search_filters)
                        VALUES (?, ?, ?, ?)
                    """, (
                        user_id,
                        json.dumps(preferences.domain_preferences) if preferences.domain_preferences else None,
                        json.dumps(preferences.topic_preferences) if preferences.topic_preferences else None,
                        json.dumps(preferences.search_filters) if preferences.search_filters else None
                    ))
                
                conn.commit()
                return True
            
        except Exception as e:
            logger.error(f"更新用户偏好失败: {str(e)}", exc_info=True)
            return False
    
    async def record_feedback(self, user_id: int, query_id: str, url: str, action: str):
        """记录用户反馈"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_feedback (user_id, query_id, url, action)
                    VALUES (?, ?, ?, ?)
                """, (user_id, query_id, url, action))
                
                conn.commit()
            
        except Exception as e:
            logger.error(f"记录用户反馈失败: {str(e)}", exc_info=True)
            raise
    
    async def _user_exists(self, username: str, email: str) -> bool:
        """检查用户是否已存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM users WHERE username = ? OR email = ?
                """, (username, email))
                
                count = cursor.fetchone()[0]
                return count > 0
            
        except Exception as e:
            logger.error(f"检查用户存在性失败: {str(e)}", exc_info=True)
            return False


# JWT令牌相关函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """获取当前登录用户（必须登录）"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService()
    user = await user_service.get_user_by_username_or_email(username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserProfile]:
    """获取当前用户（可选，允许匿名访问）"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
