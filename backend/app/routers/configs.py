from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import urllib.parse

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.schemas import ConfigResponse, ConfigContentUpdate
from app.services import config_service
from app.config import settings

router = APIRouter(prefix="/api/configs", tags=["configs"])

@router.get("", response_model=List[ConfigResponse])
def get_configs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取配置列表
    """
    return config_service.get_configs(db)

@router.post("/upload", response_model=ConfigResponse)
async def upload_config(
    name: str = Form(...),
    description: str = Form(None),
    method: str = Form("file"),
    file: UploadFile = File(None),
    url: str = Form(None),
    content: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    管理员添加配置文件（支持上传、订阅链接、粘贴内容）
    """
    if method == "file":
        if not file or not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="Only YAML files are allowed")
        return await config_service.save_config_from_file(db, file, name, description)
    elif method == "url":
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        return await config_service.save_config_from_url(db, url, name, description)
    elif method == "content":
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        return await config_service.save_config_from_content(db, content, name, description)
    else:
        raise HTTPException(status_code=400, detail="Invalid method")

@router.get("/{id}", response_model=ConfigResponse)
def get_config(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取配置详情
    """
    return config_service.get_config(db, id)

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
    config = config_service.get_config(db, id)
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
        - current_user: 当前登录用户（支持普通用户和管理员）
        
    返回:
        - JSON 对象: {"content": "..."} 包含 YAML 文件的完整文本字符串
    """
    content = await config_service.get_config_content(db, id)
    return {"content": content}

@router.put("/{id}/content", response_model=ConfigResponse)
async def update_config_content(id: int, data: ConfigContentUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    管理员更新配置内容
    """
    return await config_service.update_config_content(db, id, data.content)

@router.delete("/{id}")
def delete_config(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    管理员删除配置
    """
    config_service.delete_config(db, id)
    return {"status": "success"}
