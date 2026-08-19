from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    所有 SQLAlchemy 模型的基类
    """
    pass

class User(Base):
    """
    用户模型，用于存储管理员或普通用户的账号信息
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True) # 账号名
    role: Mapped[str] = mapped_column(String, index=True) # 角色 (admin / user)
    password_hash: Mapped[str] = mapped_column(String) # bcrypt 加密密码
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 创建时间

class Config(Base):
    """
    配置文件模型，用于记录上传的代理订阅配置文件信息
    """
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True) # 配置文件显示名称
    filename: Mapped[str] = mapped_column(String) # 实际存储文件名
    description: Mapped[str] = mapped_column(String, nullable=True) # 配置描述
    file_size: Mapped[int] = mapped_column(Integer) # 文件大小（字节）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 上传时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 最后修改时间

class ClientDownload(Base):
    """
    客户端下载缓存模型，记录从 GitHub 获取并缓存的客户端文件
    """
    __tablename__ = "client_downloads"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String, index=True) # 客户端名称 (例如：V2Ray)
    platform: Mapped[str] = mapped_column(String) # 平台 (windows/linux/macos/android)
    version: Mapped[str] = mapped_column(String) # 版本号
    filename: Mapped[str] = mapped_column(String) # 缓存文件名
    file_size: Mapped[int] = mapped_column(Integer) # 文件大小
    download_url: Mapped[str] = mapped_column(String) # GitHub 原始下载地址
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 缓存时间
