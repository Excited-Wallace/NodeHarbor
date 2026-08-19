from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 创建数据库引擎
# 对于 SQLite，需要加上 connect_args={"check_same_thread": False}，
# 因为 FastAPI 可能会在不同的线程处理同一个请求中的依赖
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI 依赖注入函数，用于获取数据库会话(Session)。
    确保在每次请求结束后关闭 session。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
