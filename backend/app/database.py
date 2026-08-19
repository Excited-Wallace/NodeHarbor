from sqlalchemy import create_engine, text, inspect
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

def migrate_database(db_engine):
    """
    数据库平滑自动迁移函数
    
    作用：
        检查已有的 SQLite 表结构，若发现新版本中新增的数据列不存在，
        自动执行 ALTER TABLE ADD COLUMN 语句补全字段，避免老数据库缺少字段报错，
        且无需手动删除数据库文件。
    """
    inspector = inspect(db_engine)
    if "configs" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("configs")]
        with db_engine.begin() as conn:
            # 1. 检查 is_public 字段
            if "is_public" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN is_public BOOLEAN DEFAULT 1"))
            # 2. 检查 subscription_url 字段
            if "subscription_url" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN subscription_url VARCHAR"))
            # 3. 检查 auto_update 字段
            if "auto_update" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN auto_update BOOLEAN DEFAULT 0"))
            # 4. 检查 update_interval_type 字段
            if "update_interval_type" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN update_interval_type VARCHAR DEFAULT 'daily'"))
            # 5. 检查 update_time 字段
            if "update_time" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN update_time VARCHAR DEFAULT '04:00'"))
            # 6. 检查 last_auto_update_at 字段
            if "last_auto_update_at" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN last_auto_update_at DATETIME"))
            # 7. 检查 last_auto_update_status 字段
            if "last_auto_update_status" not in columns:
                conn.execute(text("ALTER TABLE configs ADD COLUMN last_auto_update_status VARCHAR"))

