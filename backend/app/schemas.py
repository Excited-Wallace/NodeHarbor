from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserInfo(BaseModel):
    username: str
    role: str

class ConfigResponse(BaseModel):
    """
    配置文件的响应模型
    """
    id: int
    name: str
    filename: str
    description: Optional[str] = None
    file_size: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConfigCreate(BaseModel):
    """
    更新配置文件基础信息的模型
    """
    name: str
    description: Optional[str] = None

class ConfigContentUpdate(BaseModel):
    """
    更新配置文本内容的模型
    """
    content: str

class ClientStatusResponse(BaseModel):
    """
    客户端缓存状态的响应模型
    """
    client_name: str
    platform: str
    version: Optional[str] = None
    cached: bool
    cached_at: Optional[datetime] = None

class SystemStatusResponse(BaseModel):
    """
    系统状态响应模型
    """
    database_size: int
    configs_count: int
    downloads_size: int
    cached_clients_count: int
