"""
NodeHarbor 代理客户端下载路由 (clients.py)

文件作用：
    提供代理客户端的卡片列表查询、GitHub Release 资产获取（24小时本地缓存复用）、
    服务端异步中转缓存下载、实时下载进度轮询、已缓存安装包直接下载以及服务端缓存容量状态查询等 API。

提供的接口列表：
    1. GET  /api/clients                     - 获取 4 个支持的代理客户端基本信息卡片列表
    2. GET  /api/clients/{client_id}/release - 获取指定客户端最新 Release 及可供下载的 Assets 列表
    3. POST /api/clients/cache               - 触发服务端下载 GitHub 资产到本地缓存
    4. GET  /api/clients/tasks/{task_id}     - 查询指定服务端下载任务的实时进度与状态
    5. GET  /api/clients/download/{client_id}/{filename} - 从 NodeHarbor 服务器下载已缓存的客户端文件
    6. GET  /api/clients/cache-status        - 获取服务端当前缓存用量与限制状态
"""

import os
import urllib.parse
import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    ClientCardInfo,
    ClientReleaseInfo,
    DownloadCacheRequest,
    DownloadTaskStatus,
    CacheStorageStatus
)
from app.services import client_service

# 实例化 APIRouter
router = APIRouter(prefix="/api/clients", tags=["clients"])

@router.get("", response_model=List[ClientCardInfo])
def get_clients(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    接口：获取 4 个主流代理客户端卡片信息列表
    
    调用方法：
        GET /api/clients
        Header: Authorization: Bearer <token>
    
    返回：
        4 个客户端基础信息（v2rayN, v2rayNG, Clash Verge, Clash Meta for Android），
        包括名称、描述、平台徽章、GitHub 链接及本地已缓存版本等。
    """
    return client_service.get_clients_card_list(db)

@router.get("/{client_id}/release", response_model=ClientReleaseInfo)
async def get_client_release(
    client_id: str,
    force_refresh: bool = Query(False, description="是否强制刷新，跳过 24 小时本地缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    接口：获取指定客户端的最新 Release 详情及 Assets 列表
    
    调用方法：
        GET /api/clients/{client_id}/release?force_refresh=false
        Header: Authorization: Bearer <token>
    
    说明：
        1. 首次获取后会持久化缓存在本地数据库，24 小时内请求直接复用本地缓存；
        2. 超过 24 小时或设置 force_refresh=true 时重新请求 GitHub API；
        3. 列表中会标记各个 Asset 是否已在 NodeHarbor 服务端完成缓存（1小时有效）。
    """
    return await client_service.get_client_release_info(db, client_id, force_refresh=force_refresh)

@router.post("/cache", response_model=DownloadTaskStatus)
async def trigger_download_cache(
    request: DownloadCacheRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    接口：触发服务端中转下载 GitHub 资产到本地缓存
    
    调用方法：
        POST /api/clients/cache
        Header: Authorization: Bearer <token>
        Body: {
            "client_id": "v2rayn",
            "asset_id": "123456",
            "asset_name": "v2rayN-With-Core.zip",
            "download_url": "https://github.com/...",
            "version": "7.24.4"
        }
    
    返回：
        创建的下载任务状态与 task_id，随后可轮询 GET /api/clients/tasks/{task_id} 获取下载进度。
    """
    task_id = client_service.download_manager.create_task(
        client_id=request.client_id,
        asset_id=request.asset_id,
        asset_name=request.asset_name,
        download_url=request.download_url,
        version=request.version
    )
    
    # 异步在后台执行流式下载
    background_tasks.add_task(client_service.download_manager.run_download, task_id)
    
    task = client_service.download_manager.get_task(task_id)
    return task

@router.get("/tasks/{task_id}", response_model=DownloadTaskStatus)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    接口：轮询查询服务端异步下载任务的实时进度与状态
    
    调用方法：
        GET /api/clients/tasks/{task_id}
        Header: Authorization: Bearer <token>
    
    返回：
        任务状态（downloading/completed/failed）、已下载字节数、总大小、百分比进度及下载速度。
    """
    task = client_service.download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="下载任务不存在或已过期")
    return task

@router.get("/download/{client_id}/{filename}")
def download_cached_client(
    client_id: str,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    接口：从 NodeHarbor 服务器直接下载已缓存的客户端文件
    
    调用方法：
        GET /api/clients/download/{client_id}/{filename}
        Header: Authorization: Bearer <token>
    
    返回：
        物理文件二进制流 (FileResponse)，并在 Content-Disposition 头中指定文件名。
    """
    file_path = client_service.get_cached_file_path(db, client_id, filename)
    display_filename = os.path.basename(file_path)
    # 去除 client_id 和 version 前缀以还原原始下载文件名 (如果包含)
    parts = display_filename.split('_', 2)
    clean_name = parts[2] if len(parts) == 3 else display_filename
    
    encoded_name = urllib.parse.quote(clean_name)
    return FileResponse(
        path=file_path,
        filename=clean_name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )

@router.get("/cache-status", response_model=CacheStorageStatus)
def get_cache_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    接口：获取当前服务端安装包缓存使用状态
    
    调用方法：
        GET /api/clients/cache-status
        Header: Authorization: Bearer <token>
    
    返回：
        已占用 MB、512MB 上限限制、占用百分比、已缓存文件总数等。
    """
    return client_service.get_cache_storage_status(db)
