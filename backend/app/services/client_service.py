from sqlalchemy.orm import Session
from fastapi import HTTPException
import os
import uuid
from datetime import datetime, timedelta

from app.models import ClientDownload
from app.utils.proxy_helper import get_release_info, parse_release_assets, download_file
from app.utils.file_handler import delete_file, get_file_size
from app.config import settings

CLIENTS_MAP = {
    "v2ray": "v2fly/v2ray-core",
    "clash-verge": "clash-verge-rev/clash-verge-rev",
    "v2rayng": "2dust/v2rayNG",
    "clash-meta": "MetaCubeX/ClashMetaForAndroid"
}

def cleanup_expired(db: Session):
    """
    清理超过 1 小时的数据库记录及关联安装包文件
    """
    expire_time = datetime.utcnow() - timedelta(hours=1)
    expired_records = db.query(ClientDownload).filter(ClientDownload.cached_at < expire_time).all()
    
    for record in expired_records:
        file_path = os.path.join(settings.DOWNLOAD_DIR, record.filename)
        delete_file(file_path)
        db.delete(record)
    
    if expired_records:
        db.commit()

def get_supported_clients(db: Session):
    """
    返回支持的客户端及其在数据库中的最新缓存状态
    """
    cleanup_expired(db)
    
    results = []
    for client_name in CLIENTS_MAP.keys():
        records = db.query(ClientDownload).filter(ClientDownload.client_name == client_name).all()
        platforms = ["windows", "linux", "macos", "android"]
        
        for p in platforms:
            record = next((r for r in records if r.platform == p), None)
            if record:
                results.append({
                    "client_name": client_name,
                    "platform": p,
                    "version": record.version,
                    "cached": True,
                    "cached_at": record.cached_at
                })
            else:
                results.append({
                    "client_name": client_name,
                    "platform": p,
                    "version": None,
                    "cached": False,
                    "cached_at": None
                })
    return results

async def fetch_client(db: Session, client_name: str, platform: str) -> dict:
    """
    获取对应平台的文件下载链接，下载到本地，并记录到数据库
    """
    client_name = client_name.lower()
    if client_name not in CLIENTS_MAP:
        raise HTTPException(status_code=404, detail="Client not supported")
        
    repo = CLIENTS_MAP[client_name]
    release_info = await get_release_info(repo)
    if not release_info:
        raise HTTPException(status_code=500, detail="Failed to get release info from GitHub")
        
    version = release_info.get("tag_name", "unknown")
    assets = release_info.get("assets", [])
    
    download_url = parse_release_assets(assets, platform)
    if not download_url:
        raise HTTPException(status_code=404, detail=f"No suitable release found for {platform}")
        
    existing_record = db.query(ClientDownload).filter(
        ClientDownload.client_name == client_name,
        ClientDownload.platform == platform
    ).first()
    
    if existing_record:
        file_path = os.path.join(settings.DOWNLOAD_DIR, existing_record.filename)
        if existing_record.version == version and os.path.exists(file_path):
            existing_record.cached_at = datetime.utcnow()
            db.commit()
            return {"status": "success", "message": "Already cached latest version"}
        else:
            delete_file(file_path)
            db.delete(existing_record)
            db.commit()

    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    ext = download_url.split('/')[-1].split('.')[-1]
    filename = f"{client_name}_{platform}_{version}_{uuid.uuid4().hex[:8]}.{ext}.tmp"
    file_path = os.path.join(settings.DOWNLOAD_DIR, filename)
    
    success = await download_file(download_url, file_path)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to download client file")
        
    final_filename = filename.replace(".tmp", "")
    final_file_path = os.path.join(settings.DOWNLOAD_DIR, final_filename)
    os.rename(file_path, final_file_path)
    
    file_size = get_file_size(final_file_path)
    
    new_record = ClientDownload(
        client_name=client_name,
        platform=platform,
        version=version,
        filename=final_filename,
        file_size=file_size,
        download_url=download_url
    )
    db.add(new_record)
    db.commit()
    
    return {"status": "success", "message": "Download completed"}

def get_cached_file(db: Session, client_name: str, platform: str) -> str:
    """
    查询缓存记录，如果文件未过期则返回文件路径
    """
    cleanup_expired(db)
    
    record = db.query(ClientDownload).filter(
        ClientDownload.client_name == client_name,
        ClientDownload.platform == platform
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Cached client not found")
        
    file_path = os.path.join(settings.DOWNLOAD_DIR, record.filename)
    if not os.path.exists(file_path):
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=404, detail="Cached client file missing")
        
    return file_path
