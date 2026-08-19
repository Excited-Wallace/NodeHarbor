"""
NodeHarbor 代理订阅配置路由模块 (routers/configs.py)

文件作用：
    定义代理订阅配置相关的所有 HTTP API 接口，包括：
    - 配置列表查询（根据角色自动过滤普通用户可见项）
    - 新增配置（文件上传、外部订阅 URL 导入及定时设置、YAML 内容粘贴）
    - 快速切换配置对普通用户的可见性 (is_public)
    - 修改定时自动更新策略 (auto_update, update_time)
    - 立即手动从订阅源拉取同步配置 (sync)
    - 配置文本获取与在线编辑保存
    - 公开免登录订阅链接下载接口
    - 配置文件删除
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import urllib.parse

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.schemas import (
    ConfigResponse, 
    ConfigContentUpdate, 
    ConfigVisibilityUpdate, 
    ConfigScheduleUpdate
)
from app.services import config_service
from app.config import settings

router = APIRouter(prefix="/api/configs", tags=["configs"])

@router.get("", response_model=List[ConfigResponse])
def get_configs(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    获取代理配置文件列表
    
    权限规则：
        - 管理员：返回全部配置（包括已隐藏配置，并携带全部定时同步与可见性状态）；
        - 普通用户：仅返回 is_public == True 的公开可用配置。
    """
    is_admin = (current_user.role == "admin")
    return config_service.get_configs(db, is_admin=is_admin)

@router.post("/upload", response_model=ConfigResponse)
async def upload_config(
    name: str = Form(..., description="配置名称"),
    description: str = Form(None, description="配置描述"),
    is_public: bool = Form(True, description="是否对普通用户可见 (默认 True)"),
    method: str = Form("file", description="导入方式: file (文件) / url (订阅链接) / content (粘贴YAML)"),
    file: UploadFile = File(None, description="上传的 YAML 文件 (当 method=file 时有效)"),
    url: str = Form(None, description="订阅链接地址 (当 method=url 时有效)"),
    auto_update: bool = Form(False, description="是否开启定时自动更新 (当 method=url 时可选)"),
    update_interval_type: str = Form("daily", description="定时模式: daily / interval"),
    update_time: str = Form("04:00", description="定时时间设置 (如 '04:00' 或 '12')"),
    content: str = Form(None, description="YAML 文本内容 (当 method=content 时有效)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    管理员新增/导入配置文件
    
    接口功能：
        - 方式 1 (file): 上传本地 .yaml/.yml 配置文件；
        - 方式 2 (url): 输入外部代理订阅链接，系统自动拉取并保存，可勾选开启定时更新选项并设定时间；
        - 方式 3 (content): 直接粘贴 YAML 配置文件文本；
        - 支持同步配置 is_public 属性（控制普通用户是否可见）。
    """
    if method == "file":
        if not file or not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="仅支持上传 .yaml 或 .yml 格式的配置文件")
        return await config_service.save_config_from_file(
            db=db, 
            upload_file=file, 
            name=name, 
            description=description,
            is_public=is_public
        )
    elif method == "url":
        if not url:
            raise HTTPException(status_code=400, detail="请输入有效的订阅链接 URL")
        return await config_service.save_config_from_url(
            db=db, 
            url=url, 
            name=name, 
            description=description,
            is_public=is_public,
            auto_update=auto_update,
            update_interval_type=update_interval_type,
            update_time=update_time
        )
    elif method == "content":
        if not content:
            raise HTTPException(status_code=400, detail="请输入 YAML 文本内容")
        return await config_service.save_config_from_content(
            db=db, 
            content=content, 
            name=name, 
            description=description,
            is_public=is_public
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的导入方式")

@router.patch("/{id}/visibility", response_model=ConfigResponse)
def update_visibility(
    id: int,
    data: ConfigVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    管理员快捷切换配置文件对普通用户的可见性
    
    参数说明:
        - id: 配置文件 ID
        - data.is_public: 目标可见性 (True: 对普通用户可见, False: 仅管理员可见)
    """
    return config_service.update_config_visibility(db, id, data.is_public)

@router.put("/{id}/schedule", response_model=ConfigResponse)
def update_schedule(
    id: int,
    data: ConfigScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    管理员更新订阅配置文件的定时自动更新策略与时间
    
    参数说明:
        - id: 配置文件 ID
        - data.auto_update: 是否启用自动更新
        - data.subscription_url: 订阅链接
        - data.update_interval_type: daily / interval
        - data.update_time: 设定时刻或间隔小时数
    """
    return config_service.update_config_schedule(
        db=db,
        config_id=id,
        auto_update=data.auto_update,
        subscription_url=data.subscription_url,
        update_interval_type=data.update_interval_type,
        update_time=data.update_time
    )

@router.post("/{id}/sync", response_model=ConfigResponse)
async def sync_config(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    管理员手动立即从订阅链接拉取并更新配置文件内容
    
    接口功能：
        立即根据配置中记录的 subscription_url 发起异步请求，覆盖更新磁盘文件与文件大小。
    """
    return await config_service.sync_subscription_config(db, id)

@router.get("/{id}", response_model=ConfigResponse)
def get_config(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    获取单个配置详情（非公开配置普通用户无权查看）
    """
    is_admin = (current_user.role == "admin")
    return config_service.get_config(db, id, is_admin=is_admin)

@router.api_route("/{id}/download", methods=["GET", "HEAD"])
def download_config(id: int, db: Session = Depends(get_db)):
    """
    公开获取/下载配置文件及订阅接口（免认证，支持 Clash、Shadowrocket 等客户端直接作为订阅源拉取）
    
    接口功能：
        - 供外部代理客户端（如 Clash、Clash Verge、Clash.Meta、Shadowrocket、Sing-box 等）通过订阅链接直接获取 YAML 格式配置。
        - 供前端网页直接发起下载或无鉴权获取配置。
        
    接口调用方式：
        - 请求方法：GET
        - 请求路径：/api/configs/{id}/download
        - 示例 URL：http://localhost:8001/api/configs/1/download
        - 鉴权说明：公开端点，无需携带 Bearer Token
        
    参数说明：
        - id (int): 配置文件在数据库中的主键 ID
        - db (Session): SQLAlchemy 数据库会话（自动注入）
        
    响应内容：
        - Content-Type: text/yaml; charset=utf-8
        - Content-Disposition: inline; filename*=UTF-8''... (方便客户端直接读取内容，也支持浏览器下载)
        - profile-update-interval: 24 (建议客户端每 24 小时更新一次订阅)
    """
    config = config_service.get_config(db, id, is_admin=True)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    encoded_name = urllib.parse.quote(f"{config.name}.yaml")
    return FileResponse(
        path=file_path,
        filename=f"{config.name}.yaml",
        media_type="text/yaml; charset=utf-8",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_name}",
            "profile-update-interval": "24",
            "subscription-userinfo": "upload=0; download=0; total=107374182400; expire=0"
        }
    )

@router.get("/{id}/content")
async def get_config_content(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    获取配置文件的完整文本内容（供管理员编辑或普通用户在线查看订阅配置内容）
    
    参数说明:
        - id: 配置文件在数据库中的主键 ID
        - db: SQLAlchemy 数据库会话依赖
        - current_user: 当前登录用户（支持普通用户和管理员，普通用户仅能查看 is_public=True 的配置）
        
    返回:
        - JSON 对象: {"content": "..."} 包含 YAML 文件的完整文本字符串
    """
    is_admin = (current_user.role == "admin")
    content = await config_service.get_config_content(db, id, is_admin=is_admin)
    return {"content": content}

@router.put("/{id}/content", response_model=ConfigResponse)
async def update_config_content(
    id: int, 
    data: ConfigContentUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_admin)
):
    """
    管理员更新配置内容
    """
    return await config_service.update_config_content(db, id, data.content)

@router.delete("/{id}")
def delete_config(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_admin)
):
    """
    管理员删除配置
    """
    config_service.delete_config(db, id)
    return {"status": "success"}

