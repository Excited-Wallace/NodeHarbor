"""
NodeHarbor 数据校验与序列化模型文件 (schemas.py)

文件作用：
    定义 FastAPI 接口的请求体 (Request) 与响应体 (Response) 的 Pydantic 数据模型，
    用于数据格式校验、类型约束以及自动生成 OpenAPI 文档。

主要模块：
    1. 认证模块模型 (LoginRequest, TokenResponse, UserInfo)
    2. 订阅配置模块模型 (ConfigResponse, ConfigCreate, ConfigContentUpdate)
    3. 代理客户端下载与缓存模块模型 (ClientCardInfo, ClientReleaseAsset, ClientReleaseInfo, DownloadCacheRequest, DownloadTaskStatus, CacheStorageStatus)
    4. 系统监控模块模型 (SystemStatusResponse)
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ==========================================
# 1. 用户认证相关模型
# ==========================================

class LoginRequest(BaseModel):
    """
    登录请求模型
    
    字段说明：
        username: 用户名
        password: 登录密码
    """
    username: str = Field(..., description="登录用户名")
    password: str = Field(..., description="登录密码")

class TokenResponse(BaseModel):
    """
    JWT 登录成功响应模型
    
    字段说明：
        access_token: 签发的 JWT 访问令牌
        token_type: 令牌类型，默认为 'bearer'
        role: 用户所属角色 ('admin' 或 'user')
    """
    access_token: str
    token_type: str = "bearer"
    role: str

class UserInfo(BaseModel):
    """
    当前登录用户信息模型
    
    字段说明：
        username: 用户名
        role: 用户角色 ('admin' 或 'user')
    """
    username: str
    role: str

class UserResponse(BaseModel):
    """
    用户管理响应模型
    
    字段说明：
        id: 用户主键 ID
        username: 用户登录账号名
        role: 角色 ('admin' 或 'user')
        created_at: 账号创建时间
    """
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """
    新增用户请求模型
    
    字段说明：
        username: 账号名（必填，3-32位字符）
        password: 登录密码（必填，至少 3 位字符）
        role: 角色分配（'user' 普通用户 / 'admin' 管理员，默认为 'user'）
    """
    username: str = Field(..., min_length=2, max_length=32, description="用户登录账号名")
    password: str = Field(..., min_length=3, max_length=128, description="登录初始密码")
    role: str = Field("user", description="用户角色 (admin/user)")

class UserUpdate(BaseModel):
    """
    编辑用户/修改密码请求模型
    
    字段说明：
        password: 新密码（可选，若提供则重置密码，留空或 None 则不修改密码）
        role: 目标角色（可选，'admin' 或 'user'）
    """
    password: Optional[str] = Field(None, min_length=3, max_length=128, description="新登录密码（留空表示不修改）")
    role: Optional[str] = Field(None, description="变更用户角色 (admin/user)")

# ==========================================
# 2. 代理订阅配置相关模型
# ==========================================

class ConfigResponse(BaseModel):
    """
    订阅配置文件响应模型
    
    字段说明：
        - id: 主键 ID
        - name: 配置文件显示名称
        - filename: 存储文件名
        - description: 详细描述
        - group_name: 所属分组名称 (默认为 '默认分组')
        - file_size: 文件大小（字节）
        - is_public: 是否对普通用户可见
        - subscription_url: 原始订阅链接
        - auto_update: 是否启用定时自动更新
        - update_interval_type: 定时模式 ('daily' 每日指定时刻 / 'interval' 固定间隔小时)
        - update_time: 定时时间字符串 (如 "04:00" 或 "12")
        - last_auto_update_at: 上次自动更新时间
        - last_auto_update_status: 上次自动更新状态说明
        - created_at: 创建时间
        - updated_at: 最后更新时间
    """
    id: int
    name: str
    filename: str
    description: Optional[str] = None
    group_name: Optional[str] = "默认分组"
    file_size: int
    is_public: bool = True
    subscription_url: Optional[str] = None
    auto_update: bool = False
    update_interval_type: Optional[str] = "daily"
    update_time: Optional[str] = "04:00"
    last_auto_update_at: Optional[datetime] = None
    last_auto_update_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConfigCreate(BaseModel):
    """
    创建/更新配置文件基础信息的模型
    """
    name: str
    description: Optional[str] = None
    group_name: Optional[str] = "默认分组"
    is_public: bool = True

class ConfigGroupUpdate(BaseModel):
    """
    单条配置文件修改所属分组的请求模型
    
    字段说明：
        group_name: 目标分组名称 (如 '默认分组'、'VIP专线'、'自建节点')
    """
    group_name: str = Field(..., min_length=1, max_length=64, description="配置所属分组名称")

class ConfigBatchGroupUpdate(BaseModel):
    """
    批量调整多个配置文件分组的请求模型
    
    字段说明：
        config_ids: 待调整的配置 ID 列表
        group_name: 目标分组名称
    """
    config_ids: List[int] = Field(..., min_items=1, description="待调整分组的配置 ID 列表")
    group_name: str = Field(..., min_length=1, max_length=64, description="目标分组名称")

class ConfigGroupCreate(BaseModel):
    """
    管理员新建配置分组请求模型
    
    字段说明：
        name: 分组名称 (必填，1-64字符)
        description: 分组描述说明 (选填)
        sort_order: 排序权重 (选填，默认0)
    """
    name: str = Field(..., min_length=1, max_length=64, description="分组显示名称")
    description: Optional[str] = Field(None, max_length=255, description="分组描述说明")
    sort_order: Optional[int] = Field(0, description="排序权重 (数字越小越靠前)")

class ConfigGroupUpdateBody(BaseModel):
    """
    管理员修改配置分组信息请求模型
    
    字段说明：
        name: 新分组名称 (选填)
        description: 新分组描述说明 (选填)
        sort_order: 新排序权重 (选填)
    """
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="新分组显示名称")
    description: Optional[str] = Field(None, max_length=255, description="新分组描述说明")
    sort_order: Optional[int] = Field(None, description="排序权重")

class ConfigGroupItem(BaseModel):
    """
    分组详情及统计信息项模型
    
    字段说明：
        id: 分组 ID (如果已持久化)
        name: 分组名称
        description: 分组描述说明
        sort_order: 排序权重
        count: 该分组下的配置文件数量
        created_at: 分组创建时间
    """
    id: Optional[int] = None
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    sort_order: int = Field(0, description="排序权重")
    count: int = Field(0, description="该分组下的配置数量")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfigVisibilityUpdate(BaseModel):
    """
    修改配置文件对普通用户可见性的请求模型
    
    字段说明：
        is_public: 布尔值，True 表示普通用户可见，False 表示仅管理员可见
    """
    is_public: bool = Field(..., description="对普通用户是否可见 (True: 可见, False: 隐藏)")

class ConfigScheduleUpdate(BaseModel):
    """
    修改配置文件定时自动更新策略的请求模型
    
    字段说明：
        auto_update: 是否开启自动更新
        subscription_url: 订阅链接地址（若提供）
        update_interval_type: 更新模式 ('daily' 每日 / 'interval' 间隔)
        update_time: 设定的时间值 (如 "04:00" 或 "12")
    """
    auto_update: bool = Field(..., description="是否开启定时自动更新")
    subscription_url: Optional[str] = Field(None, description="订阅链接原始地址")
    update_interval_type: Optional[str] = Field("daily", description="定时模式: daily (每日) / interval (间隔)")
    update_time: Optional[str] = Field("04:00", description="定时时间设置 (如 04:00 或 12)")

class ConfigContentUpdate(BaseModel):
    """
    更新订阅配置文本内容的模型
    """
    content: str


# ==========================================
# 3. 代理客户端与 GitHub Release 下载缓存相关模型
# ==========================================

class ClientCardInfo(BaseModel):
    """
    客户端卡片基本信息模型（用于客户端下载首页展示 4 个卡片）
    
    字段说明：
        client_id: 客户端唯一标识 (如 v2rayn, v2rayng, clash-verge, clash-meta-android)
        name: 客户端显示名称 (如 v2rayN)
        repo: GitHub 官方开源仓库 (如 2dust/v2rayN)
        description: 客户端简介与说明
        platforms: 客户端支持的操作系统平台列表 (如 ['Windows'])
        badge: 推荐标签 (如 'Windows 首选')
        github_url: GitHub Releases 页面链接
        cached_version: 本地最新已缓存的版本号 (如果有)
    """
    client_id: str
    name: str
    repo: str
    description: str
    platforms: List[str]
    badge: str
    github_url: str
    cached_version: Optional[str] = None

class ClientReleaseAsset(BaseModel):
    """
    GitHub Release 资产文件模型
    
    字段说明：
        id: GitHub Asset 唯一 ID
        name: 资产文件名 (如 v2rayN-With-Core.zip)
        size: 文件大小 (字节)
        size_human: 格式化后的文件大小 (如 45.2 MB)
        download_url: GitHub 原始直链
        download_count: GitHub 上的下载次数
        is_cached: 当前文件是否已在 NodeHarbor 服务器上完成缓存
        cached_filename: 服务端本地缓存的文件名 (若已缓存)
        cached_expires_in: 缓存剩余有效秒数 (若已缓存，单文件 1 小时有效期)
    """
    id: str
    name: str
    size: int
    size_human: str
    download_url: str
    download_count: int = 0
    is_cached: bool = False
    cached_filename: Optional[str] = None
    cached_expires_in: Optional[int] = None

class ClientReleaseInfo(BaseModel):
    """
    GitHub Release 详情响应模型
    
    字段说明：
        client_id: 客户端标识
        client_name: 客户端名称
        repo: 对应 GitHub 仓库
        tag_name: 最新 Release 版本 Tag (如 v2.5.2)
        release_name: Release 标题
        published_at: GitHub 发布时间
        html_url: GitHub Release 页面地址
        body: Release 更新日志说明 (Markdown)
        assets: 包含的所有可供下载的 Release 资产文件列表
        from_cache: 是否命中 24 小时本地元数据缓存
        cache_fetched_at: 本地元数据缓存获取时间
    """
    client_id: str
    client_name: str
    repo: str
    tag_name: str
    release_name: Optional[str] = None
    published_at: Optional[str] = None
    html_url: str
    body: Optional[str] = None
    assets: List[ClientReleaseAsset] = []
    from_cache: bool = False
    cache_fetched_at: Optional[datetime] = None

class DownloadCacheRequest(BaseModel):
    """
    触发服务端缓存客户端文件的请求体
    
    字段说明：
        client_id: 客户端标识 (如 v2rayn)
        asset_id: GitHub 资产 ID
        asset_name: 资产文件名 (如 v2rayN-With-Core.zip)
        download_url: GitHub 原始下载链接
        version: Release 版本号 (如 7.24.4)
    """
    client_id: str
    asset_id: str
    asset_name: str
    download_url: str
    version: str

class DownloadTaskStatus(BaseModel):
    """
    服务端异步下载任务状态模型
    
    字段说明：
        task_id: 下载任务唯一 ID
        client_id: 客户端标识
        asset_name: 文件名
        status: 任务状态 ('pending' / 'downloading' / 'completed' / 'failed')
        progress: 下载进度百分比 (0 - 100)
        downloaded_bytes: 已下载字节数
        total_bytes: 文件总字节数
        speed_human: 当前下载速率 (如 '2.4 MB/s')
        filename: 下载完成后保存的文件名
        error: 错误原因 (若失败)
    """
    task_id: str
    client_id: str
    asset_name: str
    status: str
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_human: str = "0 B/s"
    filename: Optional[str] = None
    error: Optional[str] = None

class CacheStorageStatus(BaseModel):
    """
    服务端缓存容量状态模型
    
    字段说明：
        total_used_bytes: 当前已使用的缓存大小（字节）
        total_used_mb: 当前已使用的缓存大小（MB）
        max_limit_mb: 最大缓存限制（512 MB）
        usage_percent: 使用率百分比
        cached_files_count: 当前缓存的安装包文件数量
        expire_hours: 缓存有效期（1 小时）
    """
    total_used_bytes: int
    total_used_mb: float
    max_limit_mb: float = 512.0
    usage_percent: float
    cached_files_count: int
    expire_hours: int = 1

# ==========================================
# 4. 系统状态相关模型
# ==========================================

class SystemStatusResponse(BaseModel):
    """
    系统状态响应模型
    """
    database_size: int
    configs_count: int
    downloads_size: int
    cached_clients_count: int
    users_count: int = 0
