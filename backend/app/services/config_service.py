from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import uuid
import os
import aiohttp
from datetime import datetime

from app.models import Config
from app.utils.file_handler import save_upload_file, delete_file, read_file_content, write_file_content, get_file_size
from app.config import settings

async def save_config_from_file(db: Session, upload_file: UploadFile, name: str, description: str = None) -> Config:
    """
    处理文件上传并写入数据库记录 Config
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    await save_upload_file(upload_file, file_path)
    file_size = get_file_size(file_path)
    
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        file_size=file_size
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

async def save_config_from_content(db: Session, content: str, name: str, description: str = None) -> Config:
    """
    直接从文本内容保存配置并写入数据库记录 Config
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}.yaml"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    await write_file_content(file_path, content)
    file_size = get_file_size(file_path)
    
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        file_size=file_size
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

async def save_config_from_url(db: Session, url: str, name: str, description: str = None) -> Config:
    """
    从订阅链接下载并保存配置
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch subscription: {str(e)}")
        
    return await save_config_from_content(db, content, name, description)

def get_configs(db: Session):
    """
    查询所有配置文件记录
    """
    return db.query(Config).order_by(Config.created_at.desc()).all()

def get_config(db: Session, config_id: int) -> Config:
    """
    获取单个配置信息
    """
    config = db.query(Config).filter(Config.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

async def get_config_content(db: Session, config_id: int) -> str:
    """
    通过 id 查询记录，并读取文本内容
    """
    config = get_config(db, config_id)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    return await read_file_content(file_path)

async def update_config_content(db: Session, config_id: int, content: str) -> Config:
    """
    保存修改后的内容到对应的磁盘文件
    """
    config = get_config(db, config_id)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    
    await write_file_content(file_path, content)
    
    config.file_size = get_file_size(file_path)
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

def delete_config(db: Session, config_id: int):
    """
    删除数据库记录及磁盘文件
    """
    config = get_config(db, config_id)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    
    delete_file(file_path)
    db.delete(config)
    db.commit()
