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
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models import Config, ConfigGroup
from app.utils.file_handler import save_upload_file, delete_file, read_file_content, write_file_content, get_file_size
from app.config import settings
from app.database import SessionLocal

def _ensure_group_exists(db: Session, group_name: str):
    """
    辅助函数：确保指定的分组在 config_groups 实体表中存在，若不存在则自动插入
    """
    clean_name = (group_name or "").strip() or "默认分组"
    exists = db.query(ConfigGroup).filter(ConfigGroup.name == clean_name).first()
    if not exists:
        new_grp = ConfigGroup(
            name=clean_name,
            description=None,
            sort_order=0
        )
        db.add(new_grp)
        try:
            db.commit()
        except Exception:
            db.rollback()


# =========================================================================
# 1. 配置文件存储与管理核心逻辑
# =========================================================================

async def save_config_from_file(
    db: Session, 
    upload_file: UploadFile, 
    name: str, 
    description: Optional[str] = None,
    group_name: Optional[str] = "默认分组",
    is_public: bool = True
) -> Config:
    """
    处理本地 YAML 文件上传并写入数据库记录 Config
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - upload_file: 上传的文件对象
        - name: 配置文件名称
        - description: 描述信息
        - group_name: 配置所属分组名称 (默认: '默认分组')
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
    
    clean_group = (group_name or "").strip() or "默认分组"
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        group_name=clean_group,
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
    group_name: Optional[str] = "默认分组",
    is_public: bool = True
) -> Config:
    """
    直接从文本内容保存配置并写入数据库记录 Config
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - content: YAML 配置文本
        - name: 配置文件名称
        - description: 描述信息
        - group_name: 配置所属分组名称 (默认: '默认分组')
        - is_public: 是否对普通用户可见
        
    返回:
        - 新创建的 Config ORM 实例
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}.yaml"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    await write_file_content(file_path, content)
    file_size = get_file_size(file_path)
    
    clean_group = (group_name or "").strip() or "默认分组"
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        group_name=clean_group,
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
    group_name: Optional[str] = "默认分组",
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
        - group_name: 配置所属分组名称 (默认: '默认分组')
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
    
    clean_group = (group_name or "").strip() or "默认分组"
    db_config = Config(
        name=name,
        filename=filename,
        description=description,
        group_name=clean_group,
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

# 函数别名兼容
list_configs = get_configs

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

def update_config_group(db: Session, config_id: int, group_name: str) -> Config:
    """
    管理员修改指定配置的所属分组
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - config_id: 配置 ID
        - group_name: 目标分组名称（如 '默认分组'、'VIP专线' 等，若为空则自动回退为 '默认分组'）
        
    返回:
        - 更新后的 Config ORM 实例
    """
    config = get_config(db, config_id, is_admin=True)
    clean_group = (group_name or "").strip() or "默认分组"
    _ensure_group_exists(db, clean_group)
    config.group_name = clean_group
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

def batch_update_config_group(db: Session, config_ids: List[int], group_name: str) -> int:
    """
    管理员批量修改多个配置的所属分组
    
    参数说明:
        - db: SQLAlchemy 数据库会话
        - config_ids: 待修改的配置 ID 列表
        - group_name: 目标分组名称
        
    返回:
        - 实际成功更新的配置记录数量
    """
    if not config_ids:
        return 0
        
    clean_group = (group_name or "").strip() or "默认分组"
    _ensure_group_exists(db, clean_group)
    configs = db.query(Config).filter(Config.id.in_(config_ids)).all()
    count = 0
    now = datetime.utcnow()
    for cfg in configs:
        cfg.group_name = clean_group
        cfg.updated_at = now
        count += 1
    db.commit()
    return count

def create_group(db: Session, name: str, description: Optional[str] = None, sort_order: int = 0) -> ConfigGroup:
    """
    管理员新建配置分组
    
    参数说明:
        - db: 数据库会话
        - name: 分组名称
        - description: 分组描述
        - sort_order: 排序权重
        
    返回:
        - 新创建的 ConfigGroup 实例
    """
    clean_name = (name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="分组名称不能为空")
        
    existing = db.query(ConfigGroup).filter(ConfigGroup.name == clean_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"分组【{clean_name}】已存在，请勿重复创建")
        
    new_group = ConfigGroup(
        name=clean_name,
        description=description,
        sort_order=sort_order or 0
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

def update_group_info(
    db: Session, 
    group_id: int, 
    name: Optional[str] = None, 
    description: Optional[str] = None, 
    sort_order: Optional[int] = None
) -> ConfigGroup:
    """
    管理员修改配置分组元数据（重命名分组时自动同步已有配置的 group_name）
    
    参数说明:
        - db: 数据库会话
        - group_id: 分组主键 ID
        - name: 新分组名称
        - description: 新描述
        - sort_order: 新排序权重
    """
    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="指定分组不存在")
        
    old_name = group.name
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(status_code=400, detail="分组名称不能为空")
        if old_name == "默认分组" and clean_name != "默认分组":
            raise HTTPException(status_code=400, detail="系统【默认分组】不可重命名")
            
        if clean_name != old_name:
            conflict = db.query(ConfigGroup).filter(ConfigGroup.name == clean_name, ConfigGroup.id != group_id).first()
            if conflict:
                raise HTTPException(status_code=400, detail=f"已存在同名分组【{clean_name}】")
                
            # 同步更新 configs 表中所有该分组的配置
            db.query(Config).filter(Config.group_name == old_name).update(
                {"group_name": clean_name, "updated_at": datetime.utcnow()},
                synchronize_session=False
            )
            group.name = clean_name
            
    if description is not None:
        group.description = description
    if sort_order is not None:
        group.sort_order = sort_order
        
    group.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(group)
    return group

def delete_group(db: Session, group_id: int) -> bool:
    """
    管理员删除配置分组（自动将该分组下的全部配置迁移至【默认分组】）
    
    参数说明:
        - db: 数据库会话
        - group_id: 分组 ID
    """
    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="指定分组不存在")
        
    if group.name == "默认分组":
        raise HTTPException(status_code=400, detail="系统【默认分组】不允许删除")
        
    # 将该分组下的所有配置安全转移至 '默认分组'
    db.query(Config).filter(Config.group_name == group.name).update(
        {"group_name": "默认分组", "updated_at": datetime.utcnow()},
        synchronize_session=False
    )
    
    db.delete(group)
    db.commit()
    return True

def get_groups(db: Session, is_admin: bool = False) -> List[dict]:
    """
    查询系统中所有的配置分组实体及其配置数量统计
    
    权限规则:
        - 管理员: 返回全部已创建分组并统计全部配置；
        - 普通用户: 统计公开配置数量，并过滤仅返回拥有公开配置的分组（或默认分组）。
    """
    _ensure_group_exists(db, "默认分组")
    
    # 1. 统计 configs 表中每个分组的配置数量
    count_query = db.query(
        func.coalesce(Config.group_name, "默认分组").label("group_name"),
        func.count(Config.id).label("count")
    )
    if not is_admin:
        count_query = count_query.filter(Config.is_public == True)
        
    count_results = count_query.group_by(func.coalesce(Config.group_name, "默认分组")).all()
    count_map = {r.group_name: r.count for r in count_results}
    
    # 2. 查询所有的 ConfigGroup 记录
    all_groups = db.query(ConfigGroup).order_by(ConfigGroup.sort_order.asc(), ConfigGroup.id.asc()).all()
    
    # 3. 组装结果
    group_list = []
    seen_names = set()
    for g in all_groups:
        seen_names.add(g.name)
        cnt = count_map.get(g.name, 0)
        # 普通用户模式下：如果不是默认分组且数量为0，则不展示空分组
        if not is_admin and cnt == 0 and g.name != "默认分组":
            continue
            
        group_list.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "sort_order": g.sort_order,
            "count": cnt,
            "created_at": g.created_at
        })
        
    # 检查是否有 configs 中的分组未在 ConfigGroup 表中建立实体
    for g_name, cnt in count_map.items():
        if g_name not in seen_names:
            _ensure_group_exists(db, g_name)
            group_list.append({
                "id": None,
                "name": g_name,
                "description": None,
                "sort_order": 0,
                "count": cnt,
                "created_at": None
            })
            
    # 排序：默认分组排在第一位，其余按 sort_order 和名称排序
    group_list.sort(key=lambda x: (
        0 if x["name"] == "默认分组" else 1, 
        x.get("sort_order", 0) or 0, 
        x["name"]
    ))
    return group_list


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

