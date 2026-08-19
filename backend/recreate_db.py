import os
import sys
from pathlib import Path
from passlib.context import CryptContext

# 设定密码哈希的上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

sys.path.insert(0, '/root/NodeHarbor/backend')
from app.database import engine, SessionLocal
from app.models import Base, User
from app.config import settings

# 1. 删除旧的数据库文件
db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
if db_path.exists():
    os.remove(db_path)
    print(f"Deleted old database at {db_path}")

# 2. 重新创建表结构
Base.metadata.create_all(bind=engine)
print("Created new tables.")

# 3. 插入初始账号
db = SessionLocal()
try:
    admin_user = User(
        username="admin",
        role="admin",
        password_hash=pwd_context.hash("admin")
    )
    normal_user = User(
        username="user",
        role="user",
        password_hash=pwd_context.hash("user")
    )
    db.add(admin_user)
    db.add(normal_user)
    db.commit()
    print("Inserted initial admin and user accounts.")
except Exception as e:
    db.rollback()
    print(f"Failed to insert users: {e}")
finally:
    db.close()
