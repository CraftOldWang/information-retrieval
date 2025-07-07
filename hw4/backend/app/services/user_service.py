import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.models.user import User, UserPreferences, UserFeedback
from app.models.base import Base, engine
from app.schemas.user import UserCreate, UserLogin, UserProfile, UserPreferencesResponse

logger = logging.getLogger(__name__)

class UserService:
    """用户服务类，使用单例模式"""
    _instance = None
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """初始化用户服务"""
        try:
            # 创建数据库表
            Base.metadata.create_all(bind=engine)
            logger.info("User service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize user service: {e}")
            raise e
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self._pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return self._pwd_context.hash(password)
    
    def create_access_token(self, user_id: int) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    async def create_user(self, db: Session, user_create: UserCreate) -> User:
        """创建用户"""
        try:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == user_create.username).first()
            if existing_user:
                raise BadRequestException("Username already exists")
            
            # 创建用户
            db_user = User(
                username=user_create.username,
                hashed_password=self.get_password_hash(user_create.password),
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # 创建用户偏好设置
            db_preferences = UserPreferences(
                user_id=db_user.id,
                preferred_domains=[],
                excluded_domains=[],
                preferred_topics=[],
                search_history_enabled=True,
                personalized_search_enabled=True,
            )
            db.add(db_preferences)
            db.commit()
            
            return db_user
        except IntegrityError:
            db.rollback()
            raise BadRequestException("Database integrity error")
        except Exception as e:
            db.rollback()
            logger.error(f"Create user error: {e}")
            raise BadRequestException(f"Create user error: {str(e)}")
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> User:
        """认证用户"""
        user = db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.hashed_password):
            raise UnauthorizedException("Incorrect username or password")
        return user
    
    async def get_user_profile(self, db: Session, user_id: int) -> User:
        """获取用户资料"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestException("User not found")
        return user
    
    async def get_user_preferences(self, db: Session, user_id: int) -> UserPreferences:
        """获取用户偏好设置"""
        preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if not preferences:
            # 如果不存在，则创建默认偏好设置
            preferences = UserPreferences(
                user_id=user_id,
                preferred_domains=[],
                excluded_domains=[],
                preferred_topics=[],
                search_history_enabled=True,
                personalized_search_enabled=True,
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        return preferences
    
    async def update_user_preferences(self, db: Session, user_id: int, preferences_data: Dict[str, Any]) -> UserPreferences:
        """更新用户偏好设置"""
        preferences = await self.get_user_preferences(db, user_id)
        
        # 更新偏好设置
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        db.commit()
        db.refresh(preferences)
        return preferences
    
    async def add_user_feedback(self, db: Session, user_id: int, document_id: str, feedback_type: str) -> UserFeedback:
        """添加用户反馈"""
        # 检查是否已存在相同的反馈
        existing_feedback = db.query(UserFeedback).filter(
            UserFeedback.user_id == user_id,
            UserFeedback.document_id == document_id,
            UserFeedback.feedback_type == feedback_type
        ).first()
        
        if existing_feedback:
            # 如果已存在，则更新时间戳
            existing_feedback.timestamp = datetime.utcnow()
            db.commit()
            db.refresh(existing_feedback)
            return existing_feedback
        
        # 创建新的反馈
        feedback = UserFeedback(
            user_id=user_id,
            document_id=document_id,
            feedback_type=feedback_type,
            timestamp=datetime.utcnow()
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    
    async def get_user_feedback(self, db: Session, user_id: int, limit: int = 100) -> List[UserFeedback]:
        """获取用户反馈"""
        return db.query(UserFeedback).filter(UserFeedback.user_id == user_id).order_by(UserFeedback.timestamp.desc()).limit(limit).all()