"""
NodeHarbor 数据模型定义文件 (models.py)

文件作用：
    定义系统中所有的 SQLAlchemy ORM 数据模型，包括用户、配置文件、客户端下载缓存以及 GitHub Release 元数据缓存等。

包含的模型：
    1. User: 用户账号与角色模型 (admin/user)
    2. Config: 代理订阅配置文件模型
    3. ClientDownload: 服务端已缓存的客户端二进制安装包文件模型 (缓存有效期 1 小时，最大 512MB)
    4. ClientReleaseCache: GitHub Release 元数据缓存模型 (缓存有效期 24 小时)
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
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
    客户端安装包下载缓存模型
    
    作用：
        记录从 GitHub 下载并缓存在服务器 downloads/ 目录下的安装包物理文件。
        用于控制单文件 1 小时缓存有效期以及总缓存不超过 512MB 的容量限制。
    """
    __tablename__ = "client_downloads"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String, index=True) # 客户端标识 (如 v2rayn, v2rayng, clash-verge, clash-meta-android)
    asset_id: Mapped[str] = mapped_column(String, index=True, nullable=True) # GitHub Asset ID
    platform: Mapped[str] = mapped_column(String, nullable=True) # 平台标识 (如 windows, android, macos, linux 等)
    version: Mapped[str] = mapped_column(String) # 版本号 (如 7.24.4, 2.2.6, v2.5.2)
    filename: Mapped[str] = mapped_column(String) # 缓存保存在本地磁盘的文件名
    file_size: Mapped[int] = mapped_column(Integer) # 文件大小（字节数）
    download_url: Mapped[str] = mapped_column(String) # GitHub 原始下载直链
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 缓存保存时间（用于 1 小时过期判断）

class ClientReleaseCache(Base):
    """
    GitHub Release 列表与资产元数据本地缓存模型
    
    作用：
        缓存从 GitHub API 获取的仓库最新 Release 元数据（包含 Assets 列表和下载链接），
        有效期为 24 小时。在有效期内直接复用本地缓存，避免频繁请求 GitHub 触发 API 限流。
    """
    __tablename__ = "client_release_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String, unique=True, index=True) # 客户端标识 (如 v2rayn, v2rayng, clash-verge, clash-meta-android)
    tag_name: Mapped[str] = mapped_column(String) # 最新 Release Tag (如 v2.5.2)
    release_name: Mapped[str] = mapped_column(String, nullable=True) # Release 标题
    published_at: Mapped[str] = mapped_column(String, nullable=True) # GitHub 发布时间字符串
    html_url: Mapped[str] = mapped_column(String) # GitHub Release 页面地址
    body: Mapped[str] = mapped_column(Text, nullable=True) # 更新日志文本
    assets_json: Mapped[str] = mapped_column(Text) # JSON 序列化的全部资产列表 (包含 id, name, size, download_url 等)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 上次从 GitHub 抓取的时间（24小时失效）
