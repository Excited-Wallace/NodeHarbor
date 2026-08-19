"""
NodeHarbor 代理订阅配置文件服务层 (config_service.py)

文件作用：
    提供代理订阅配置文件的上传、下载、修改、删除、普通用户可见性控制，
    以及针对订阅链接配置的定时自动同步与后台异步轮询调度功能。

核心功能：
    1. save_config_from_file: 本地 YAML 文件上传存储
    2. save_config_from_content: 文本直接粘贴 YAML 保存
    3. save_config_from_url: 从外部订阅链接抓取并保存（支持配置定时自动更新）
    4. get_configs: 获取配置文件列表（根据用户角色自动过滤公开/隐藏配置）
    5. update_config_visibility: 切换配置对普通用户的可见性 (is_public)
    6. update_config_schedule: 修改配置的定时自动更新参数
    7. sync_subscription_config: 立即手动同步外部订阅链接最新内容
    8. background_config_update_scheduler: 后台异步定时更新调度 Worker
"""

import os
import uuid
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models import Config
from app.utils.file_handler import save_upload_file, delete_file, read_file_content, write_file_content, get_file_size
from app.config import settings
from app.database import SessionLocal

# =========================================================================
# 1. 配置文件存储与管理核心逻辑
# =========================================================================

async def save_config_from_file(
    db: Session, 
    upload_file: UploadFile, 
    name: str, 
    description: Optional[str] = None,
    is_public: bool = True
) -> Config:
    """
    处理本地 YAML 文件上传并写入数据库记录 Config
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - upload_file: 上传的文件对象
        - name: 配置文件名称
        - description: 描述信息
        - is_public: 是否对普通用户可见
        
    返回:
        - 新创建的 Config ORM 实例
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    ext = os.path.splitext(upload_file.filename)[1]
    if not ext:
        ext = ".yaml"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    await save_upload_file(upload_file, file_path)
    file_size = get_file_size(file_path)
    
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        file_size=file_size,
        is_public=is_public,
        auto_update=False
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

async def save_config_from_content(
    db: Session, 
    content: str, 
    name: str, 
    description: Optional[str] = None,
    is_public: bool = True
) -> Config:
    """
    直接从文本内容保存配置并写入数据库记录 Config
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - content: YAML 配置文本
        - name: 配置文件名称
        - description: 描述信息
        - is_public: 是否对普通用户可见
        
    返回:
        - 新创建的 Config ORM 实例
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
        file_size=file_size,
        is_public=is_public,
        auto_update=False
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

async def save_config_from_url(
    db: Session, 
    url: str, 
    name: str, 
    description: Optional[str] = None,
    is_public: bool = True,
    auto_update: bool = False,
    update_interval_type: str = "daily",
    update_time: str = "04:00"
) -> Config:
    """
    从外部订阅链接抓取并保存配置（支持配置定时自动更新）
    
    参数说明:
        - db: 数据库会话
        - url: 订阅链接地址
        - name: 配置名称
        - description: 配置描述
        - is_public: 是否对普通用户可见
        - auto_update: 是否开启后台定时自动更新
        - update_interval_type: 定时模式 ('daily' / 'interval')
        - update_time: 设定的时间（如 '04:00' 或 '12'）
        
    返回:
        - 新创建的 Config ORM 实例
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                response.raise_for_status()
                content = await response.text()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"拉取订阅配置失败: {str(e)}")
        
    filename = f"{uuid.uuid4().hex}.yaml"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    await write_file_content(file_path, content)
    file_size = get_file_size(file_path)
    
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        file_size=file_size,
        is_public=is_public,
        subscription_url=url,
        auto_update=auto_update,
        update_interval_type=update_interval_type if auto_update else "daily",
        update_time=update_time if auto_update else "04:00",
        last_auto_update_at=datetime.utcnow() if auto_update else None,
        last_auto_update_status="success" if auto_update else None
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_configs(db: Session, is_admin: bool = False) -> List[Config]:
    """
    查询配置文件列表
    
    权限规则:
        - 如果是管理员 (is_admin=True)，返回系统中全部配置；
        - 如果是普通用户 (is_admin=False)，过滤仅返回 is_public=True 的配置。
    """
    query = db.query(Config)
    if not is_admin:
        query = query.filter(Config.is_public == True)
    return query.order_by(Config.created_at.desc()).all()

def get_config(db: Session, config_id: int, is_admin: bool = True) -> Config:
    """
    获取单个配置文件详情
    
    参数:
        - is_admin: 是否为管理员，非管理员若访问非公开配置将抛出 403
    """
    config = db.query(Config).filter(Config.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置文件不存在")
    if not is_admin and not config.is_public:
        raise HTTPException(status_code=403, detail="该配置文件未对普通用户公开")
    return config

async def get_config_content(db: Session, config_id: int, is_admin: bool = True) -> str:
    """
    通过 id 查询记录，并读取磁盘文本内容
    """
    config = get_config(db, config_id, is_admin=is_admin)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="磁盘上的配置文件已丢失")
    return await read_file_content(file_path)

async def update_config_content(db: Session, config_id: int, content: str) -> Config:
    """
    保存修改后的文本内容到对应的磁盘文件，并刷新 updated_at 与 file_size
    """
    config = get_config(db, config_id, is_admin=True)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    
    await write_file_content(file_path, content)
    
    config.file_size = get_file_size(file_path)
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

def update_config_visibility(db: Session, config_id: int, is_public: bool) -> Config:
    """
    管理员快捷切换配置对普通用户的可见性
    
    参数说明:
        - config_id: 配置 ID
        - is_public: 目标可见性状态
    """
    config = get_config(db, config_id, is_admin=True)
    config.is_public = is_public
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

def update_config_schedule(
    db: Session, 
    config_id: int, 
    auto_update: bool, 
    subscription_url: Optional[str] = None,
    update_interval_type: Optional[str] = "daily",
    update_time: Optional[str] = "04:00"
) -> Config:
    """
    管理员更新配置文件的定时自动更新策略
    
    参数说明:
        - auto_update: 是否启用自动更新
        - subscription_url: 原始订阅链接
        - update_interval_type: 模式 ('daily' / 'interval')
        - update_time: 设定时间字符串
    """
    config = get_config(db, config_id, is_admin=True)
    config.auto_update = auto_update
    if subscription_url is not None:
        config.subscription_url = subscription_url
    if update_interval_type is not None:
        config.update_interval_type = update_interval_type
    if update_time is not None:
        config.update_time = update_time
        
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

async def sync_subscription_config(db: Session, config_id: int) -> Config:
    """
    手动或定时触发：从 subscription_url 抓取最新内容并静默覆写更新本地配置文件
    
    处理步骤：
        1. 检查配置是否具有有效的 subscription_url；
        2. 使用 aiohttp 异步请求拉取最新配置；
        3. 写入磁盘并更新数据库元数据 (file_size, updated_at, last_auto_update_at, last_auto_update_status)。
    """
    config = get_config(db, config_id, is_admin=True)
    if not config.subscription_url:
        raise HTTPException(status_code=400, detail="该配置未绑定订阅链接，无法同步")
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.subscription_url, timeout=aiohttp.ClientTimeout(total=25)) as response:
                response.raise_for_status()
                content = await response.text()
                
        file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
        await write_file_content(file_path, content)
        
        config.file_size = get_file_size(file_path)
        config.updated_at = datetime.utcnow()
        config.last_auto_update_at = datetime.utcnow()
        config.last_auto_update_status = "success"
        db.commit()
        db.refresh(config)
        return config
    except Exception as e:
        error_msg = f"同步失败: {str(e)}"
        config.last_auto_update_status = error_msg
        db.commit()
        db.refresh(config)
        raise HTTPException(status_code=400, detail=error_msg)

def delete_config(db: Session, config_id: int):
    """
    删除数据库记录及磁盘文件
    """
    config = get_config(db, config_id, is_admin=True)
    file_path = os.path.join(settings.UPLOAD_DIR, config.filename)
    
    delete_file(file_path)
    db.delete(config)
    db.commit()

# =========================================================================
# 2. 后台异步定时更新调度 Worker (每 30 秒轮询)
# =========================================================================

def _should_update_config(config: Config, now: datetime) -> bool:
    """
    判断指定配置在当前时刻是否满足定时更新条件
    
    规则：
        - daily: 每日在指定时刻 (如 04:00) 执行一次
          如果当前时间处于 HH:MM 时刻，且今天（或过去 20 小时内）尚未成功更新过，则触发。
        - interval: 每隔 X 小时执行一次
          如果 (now - last_auto_update_at) >= X 小时（若未更新过则从 created_at 起算），则触发。
    """
    if not config.auto_update or not config.subscription_url:
        return False
        
    interval_type = config.update_interval_type or "daily"
    time_val = config.update_time or "04:00"
    
    if interval_type == "daily":
        try:
            parts = time_val.strip().split(":")
            target_hour = int(parts[0])
            target_minute = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            target_hour, target_minute = 4, 0
            
        # 当前系统 UTC 时间或本地时间的时分匹配
        # 这里统一按系统当前时间计算
        current_hour = now.hour
        current_minute = now.minute
        
        # 判断时间是否匹配当前分钟
        if current_hour == target_hour and current_minute == target_minute:
            # 检查在过去 20 小时内是否已经更新过，避免同一分钟内被 30 秒轮询重复触发
            if not config.last_auto_update_at:
                return True
            time_diff = (now - config.last_auto_update_at).total_seconds()
            return time_diff >= 20 * 3600
        return False
        
    elif interval_type == "interval":
        try:
            interval_hours = float(time_val)
        except Exception:
            interval_hours = 12.0
            
        base_time = config.last_auto_update_at or config.created_at
        if not base_time:
            return True
        time_diff = (now - base_time).total_seconds()
        return time_diff >= interval_hours * 3600
        
    return False

async def background_config_update_scheduler():
    """
    后台定时更新调度器 Worker
    
    运行机制:
        - 每 30 秒唤起一次循环；
        - 扫描所有 auto_update 为 True 且具有 subscription_url 的配置；
        - 调用 _should_update_config 决策是否触发拉取；
        - 若触发，异步拉取并写入磁盘，记录状态与更新时间。
    """
    while True:
        try:
            await asyncio.sleep(30)
            now = datetime.utcnow()
            db = SessionLocal()
            try:
                configs = db.query(Config).filter(
                    Config.auto_update == True,
                    Config.subscription_url != None
                ).all()
                
                for cfg in configs:
                    if _should_update_config(cfg, now):
                        try:
                            # 异步拉取订阅最新配置并覆盖
                            async with aiohttp.ClientSession() as session:
                                async with session.get(cfg.subscription_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                                    if response.status == 200:
                                        content = await response.text()
                                        file_path = os.path.join(settings.UPLOAD_DIR, cfg.filename)
                                        await write_file_content(file_path, content)
                                        
                                        cfg.file_size = get_file_size(file_path)
                                        cfg.updated_at = datetime.utcnow()
                                        cfg.last_auto_update_at = datetime.utcnow()
                                        cfg.last_auto_update_status = "success"
                                        db.commit()
                                        print(f"[AutoUpdate] 配置 '{cfg.name}' (ID: {cfg.id}) 自动更新成功")
                                    else:
                                        cfg.last_auto_update_status = f"HTTP {response.status}"
                                        db.commit()
                        except Exception as sync_err:
                            cfg.last_auto_update_status = f"error: {str(sync_err)}"
                            db.commit()
                            print(f"[AutoUpdate] 配置 '{cfg.name}' (ID: {cfg.id}) 自动更新异常: {sync_err}")
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[AutoUpdate Scheduler Exception]: {e}")
            await asyncio.sleep(10)

