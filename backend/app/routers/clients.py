from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import urllib.parse

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User
from app.schemas import ClientStatusResponse
from app.services import client_service

router = APIRouter(prefix="/api/clients", tags=["clients"])

@router.get("", response_model=List[ClientStatusResponse])
def get_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    返回支持的客户端状态列表
    """
    return client_service.get_supported_clients(db)

@router.post("/{name}/fetch")
async def fetch_client(name: str, platform: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    触发从 GitHub 获取客户端（异步进行）
    """
    background_tasks.add_task(client_service.fetch_client, db, name, platform)
    return {"status": "started", "message": f"Started fetching {name} for {platform}"}

@router.get("/{name}/download")
def download_client(name: str, platform: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    下载已缓存的客户端文件
    """
    file_path = client_service.get_cached_file(db, name, platform)
    filename = os.path.basename(file_path)
    encoded_name = urllib.parse.quote(filename)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )
