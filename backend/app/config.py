import os
from pathlib import Path

# 获取项目根目录 (backend目录)
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库文件存放目录
DATA_DIR = BASE_DIR / "data"

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 默认数据库 URL
DEFAULT_DATABASE_URL = f"sqlite:///{DATA_DIR}/nodeharbor.db"

class Settings:
    """
    项目配置类，用于集中管理全局配置变量
    """
    # 数据库连接字符串，优先从环境变量读取，如果没有则使用默认 SQLite 路径
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    
    # 以下配置为预留给后续模块使用
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # Token 默认过期时间 (7天)
    
    # 路径配置
    DATA_DIR = DATA_DIR
    UPLOAD_DIR = BASE_DIR / "uploads"
    DOWNLOAD_DIR = BASE_DIR / "downloads"

settings = Settings()
