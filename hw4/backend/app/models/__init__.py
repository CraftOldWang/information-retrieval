# 首先导入基础类
from .base import Base, engine, SessionLocal

# 然后导入其他模型
from .user import User, UserPreferences, UserFeedback
from .history import SearchHistory, Snapshot

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)