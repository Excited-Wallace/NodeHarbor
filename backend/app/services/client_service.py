"""
NodeHarbor 代理客户端服务层 (client_service.py)

文件作用：
    提供 4 个主流代理客户端的元数据配置、GitHub Release 抓取与 24 小时本地缓存、
    安装包服务端异步流式中转下载、实时下载进度跟踪、1 小时缓存过期清理以及 512MB 容量限制控制等核心业务逻辑。

核心模块：
    1. 客户端静态元数据字典 CLIENTS_META
    2. Release 元数据 24 小时持久缓存管理
    3. 异步下载任务管理器 DownloadTaskManager
    4. 缓存容量上限 (512MB) 与过期时间 (1小时) 清理逻辑
    5. 后台异步定时清理任务 Worker
"""

import os
import json
import time
import uuid
import asyncio
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import ClientDownload, ClientReleaseCache
from app.config import settings
from app.database import SessionLocal
from app.utils.file_handler import delete_file, get_file_size

# 缓存配置常量
MAX_CACHE_BYTES = 512 * 1024 * 1024  # 512MB 最大缓存限制
CACHE_EXPIRE_HOURS = 1                # 客户端安装包缓存有效期：1 小时
RELEASE_CACHE_EXPIRE_HOURS = 24       # GitHub Release 元数据缓存有效期：24 小时

# 4 个官方支持的代理客户端元数据配置
CLIENTS_META = {
    "v2rayn": {
        "client_id": "v2rayn",
        "name": "v2rayN",
        "repo": "2dust/v2rayN",
        "description": "桌面平台主流代理客户端，支持 Xray / V2Ray / Sing-box 等多种内核与丰富路由规则",
        "platforms": ["Desktop"],
        "badge": "跨平台桌面端",
        "github_url": "https://github.com/2dust/v2rayN/releases"
    },
    "v2rayng": {
        "client_id": "v2rayng",
        "name": "v2rayNG",
        "repo": "2dust/v2rayNG",
        "description": "Android 平台主流代理客户端，支持分应用代理、智能路由及多种主流协议",
        "platforms": ["Android"],
        "badge": "Android ",
        "github_url": "https://github.com/2dust/v2rayNG/releases"
    },
    "clash-verge": {
        "client_id": "clash-verge",
        "name": "Clash Verge",
        "repo": "clash-verge-rev/clash-verge-rev",
        "description": "基于 Tauri 跨平台现代化客户端，适配 Clash Meta (Mihomo) 内核，界面美观优雅且性能强劲",
        "platforms": ["Desktop"],
        "badge": "跨平台桌面端",
        "github_url": "https://github.com/clash-verge-rev/clash-verge-rev/releases"
    },
    "clash-meta-android": {
        "client_id": "clash-meta-android",
        "name": "Clash Meta for Android",
        "repo": "MetaCubeX/ClashMetaForAndroid",
        "description": "Android 平台 Clash.Meta (Mihomo) 客户端，支持最新规则集、分流配置与扩展协议",
        "platforms": ["Android"],
        "badge": "Android ",
        "github_url": "https://github.com/MetaCubeX/ClashMetaForAndroid/releases"
    }
}

def format_file_size(size_bytes: int) -> str:
    """
    将字节数格式化为人类可读的大小 (B / KB / MB / GB)
    
    参数:
        size_bytes: 文件大小（字节）
    返回:
        格式化后的字符串 (如 '45.2 MB')
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def is_valid_installer_asset(filename: str) -> bool:
    """
    判断 GitHub Release Asset 文件是否为合法的客户端安装包格式。
    
    规则：
        1. 必须属于支持的安装包文件后缀白名单：
           .exe, .msi, .zip, .rar, .7z, .tar, .tar.gz, .tar.xz, .tgz, .deb, .apk, .dmg, .pkg, .appimage, .rpm
        2. 严格过滤掉非安装包格式（如 .asc, .sig, .sha256, .sha1, .md5, .txt, .json, .yml, .yaml, .blockmap 等）。
    
    参数:
        filename: 文件名字符串 (如 'v2rayN-With-Core.zip' 或 'v2rayN.zip.dgst')
    返回:
        True 如果是合法的安装包，False 如果是非安装包文件
    """
    if not filename:
        return False
    fn = filename.lower().strip()
    
    # 明确排除的签名、哈希校验及文本等非安装包黑名单后缀
    invalid_suffixes = (
        '.asc', '.sig', '.dgst', '.sha256', '.sha256sum', '.sha512', 
        '.sha1', '.md5', '.txt', '.json', '.yml', '.yaml', '.blockmap', 
        '.sbom', '.license', '.torrent', '.diff'
    )
    if any(fn.endswith(ext) for ext in invalid_suffixes):
        return False
        
    # 合法的客户端安装包格式白名单
    valid_suffixes = (
        '.exe', '.msi', '.zip', '.rar', '.7z', '.tar', 
        '.tar.gz', '.tar.xz', '.tgz', '.deb', '.apk', 
        '.dmg', '.pkg', '.appimage', '.rpm'
    )
    return any(fn.endswith(ext) for ext in valid_suffixes)

# =========================================================================
# 1. 缓存清理与容量控制 (1 小时过期，512MB 超限清空)
# =========================================================================

def cleanup_expired_and_oversized_cache(db: Session) -> dict:
    """
    执行缓存生命周期管理与空间控制：
    1. 自动删除创建时间超过 1 小时的文件及数据库记录；
    2. 清理磁盘孤儿临时文件；
    3. 检查缓存目录总大小，若超过 512MB，则清空所有缓存文件及记录。
    
    参数:
        db: SQLAlchemy 数据库会话
    返回:
        清理统计结果字典
    """
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    now = datetime.utcnow()
    expire_threshold = now - timedelta(hours=CACHE_EXPIRE_HOURS)
    
    deleted_expired_count = 0
    cleared_all = False
    
    # 步骤 1: 清理超过 1 小时的过期记录
    expired_records = db.query(ClientDownload).filter(ClientDownload.cached_at < expire_threshold).all()
    for record in expired_records:
        file_path = os.path.join(settings.DOWNLOAD_DIR, record.filename)
        delete_file(file_path)
        db.delete(record)
        deleted_expired_count += 1
    
    if expired_records:
        db.commit()

    # 步骤 2: 清理过期的 .tmp 临时下载残留文件（超过 15 分钟未完成的临时文件）
    for item in os.listdir(settings.DOWNLOAD_DIR):
        if item.endswith(".tmp"):
            tmp_path = os.path.join(settings.DOWNLOAD_DIR, item)
            try:
                mtime = os.path.getmtime(tmp_path)
                if time.time() - mtime > 900:  # 15分钟
                    delete_file(tmp_path)
            except Exception:
                pass

    # 步骤 3: 检查 downloads 目录当前总占用大小
    total_size = 0
    all_files = []
    for root, _, files in os.walk(settings.DOWNLOAD_DIR):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                sz = os.path.getsize(fp)
                total_size += sz
                all_files.append(fp)

    # 若总大小超出 512MB，清空全部缓存文件并清空数据库记录
    if total_size > MAX_CACHE_BYTES:
        for fp in all_files:
            delete_file(fp)
        db.query(ClientDownload).delete()
        db.commit()
        cleared_all = True
        total_size = 0

    return {
        "deleted_expired_count": deleted_expired_count,
        "cleared_all_due_to_limit": cleared_all,
        "current_total_size": total_size
    }

def get_cache_storage_status(db: Session) -> dict:
    """
    查询服务端缓存使用情况
    
    参数:
        db: SQLAlchemy 数据库会话
    返回:
        容量统计信息
    """
    cleanup_expired_and_oversized_cache(db)
    
    total_size = 0
    if os.path.exists(settings.DOWNLOAD_DIR):
        for root, _, files in os.walk(settings.DOWNLOAD_DIR):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)

    count = db.query(ClientDownload).count()
    used_mb = round(total_size / (1024 * 1024), 2)
    usage_percent = round((total_size / MAX_CACHE_BYTES) * 100, 2)

    return {
        "total_used_bytes": total_size,
        "total_used_mb": used_mb,
        "max_limit_mb": 512.0,
        "usage_percent": min(usage_percent, 100.0),
        "cached_files_count": count,
        "expire_hours": CACHE_EXPIRE_HOURS
    }

# =========================================================================
# 2. 客户端卡片列表与 Release 获取（24小时本地缓存复用）
# =========================================================================

def get_clients_card_list(db: Session) -> List[dict]:
    """
    获取 4 个客户端的卡片列表及本地最新缓存状态
    
    参数:
        db: SQLAlchemy 数据库会话
    返回:
        客户端卡片信息列表
    """
    cleanup_expired_and_oversized_cache(db)
    
    cards = []
    for client_id, meta in CLIENTS_META.items():
        # 查询本地是否已有该客户端的已缓存安装包
        latest_download = db.query(ClientDownload).filter(
            ClientDownload.client_name == client_id
        ).order_by(ClientDownload.cached_at.desc()).first()
        
        cards.append({
            "client_id": meta["client_id"],
            "name": meta["name"],
            "repo": meta["repo"],
            "description": meta["description"],
            "platforms": meta["platforms"],
            "badge": meta["badge"],
            "github_url": meta["github_url"],
            "cached_version": latest_download.version if latest_download else None
        })
    return cards

async def fetch_github_release(repo: str) -> dict:
    """
    通过 GitHub API 异步拉取指定仓库的最新发布信息
    
    参数:
        repo: GitHub 仓库全名 (如 '2dust/v2rayN')
    返回:
        GitHub Release JSON 字典
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "User-Agent": "NodeHarbor-ProxyClientManager/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    # 如果系统配置了 GITHUB_TOKEN，则自动附带以提升 API 速率限制
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 403:
                raise HTTPException(status_code=429, detail="GitHub API 速率受限，请稍后重试")
            elif response.status == 404:
                raise HTTPException(status_code=404, detail=f"GitHub 仓库 {repo} 未找到 Release")
            else:
                raise HTTPException(status_code=502, detail=f"获取 GitHub Release 失败，状态码: {response.status}")

async def get_client_release_info(db: Session, client_id: str, force_refresh: bool = False) -> dict:
    """
    获取指定客户端的最新 Release 及 Assets 列表。
    
    策略：
        1. 优先检查本地数据库中的 24 小时元数据缓存；
        2. 若在 24 小时有效期内且未强制刷新，直接复用本地缓存的 Release 及下载链接；
        3. 若超过 24 小时或本地无记录，则重新请求 GitHub API 并更新本地缓存；
        4. 关联查询服务端本地已缓存的实际安装包文件状态（1小时有效）。
    
    参数:
        db: SQLAlchemy 数据库会话
        client_id: 客户端标识 (如 'v2rayn')
        force_refresh: 是否强制跳过本地 24 小时缓存直接从 GitHub 重新拉取
    返回:
        Release 完整详情与资产列表
    """
    client_id = client_id.lower()
    if client_id not in CLIENTS_META:
        raise HTTPException(status_code=404, detail=f"不支持的客户端: {client_id}")
        
    meta = CLIENTS_META[client_id]
    repo = meta["repo"]
    now = datetime.utcnow()
    release_expire_threshold = now - timedelta(hours=RELEASE_CACHE_EXPIRE_HOURS)
    
    # 查找本地持久化的 Release 缓存
    cached_release = db.query(ClientReleaseCache).filter(
        ClientReleaseCache.client_name == client_id
    ).first()
    
    use_local_cache = False
    release_data = None
    
    if cached_release and not force_refresh and cached_release.fetched_at >= release_expire_threshold:
        use_local_cache = True
        try:
            raw_assets = json.loads(cached_release.assets_json)
            release_data = {
                "tag_name": cached_release.tag_name,
                "name": cached_release.release_name or cached_release.tag_name,
                "published_at": cached_release.published_at,
                "html_url": cached_release.html_url,
                "body": cached_release.body,
                "assets": raw_assets,
                "fetched_at": cached_release.fetched_at
            }
        except Exception:
            use_local_cache = False

    # 若未命中 24 小时本地缓存，则请求 GitHub API
    if not use_local_cache or not release_data:
        gh_data = await fetch_github_release(repo)
        tag_name = gh_data.get("tag_name", "latest")
        rel_name = gh_data.get("name") or tag_name
        pub_at = gh_data.get("published_at")
        html_url = gh_data.get("html_url") or meta["github_url"]
        body = gh_data.get("body", "")
        
        # 提取 Assets 关键字段，仅保留合法的安装包格式
        raw_assets = []
        for asset in gh_data.get("assets", []):
            aname = asset.get("name", "")
            if is_valid_installer_asset(aname):
                raw_assets.append({
                    "id": str(asset.get("id")),
                    "name": aname,
                    "size": asset.get("size", 0),
                    "download_url": asset.get("browser_download_url"),
                    "download_count": asset.get("download_count", 0)
                })
            
        assets_json_str = json.dumps(raw_assets, ensure_ascii=False)
        
        # 更新或写入数据库 Release 缓存表
        if cached_release:
            cached_release.tag_name = tag_name
            cached_release.release_name = rel_name
            cached_release.published_at = pub_at
            cached_release.html_url = html_url
            cached_release.body = body
            cached_release.assets_json = assets_json_str
            cached_release.fetched_at = now
        else:
            new_cache = ClientReleaseCache(
                client_name=client_id,
                tag_name=tag_name,
                release_name=rel_name,
                published_at=pub_at,
                html_url=html_url,
                body=body,
                assets_json=assets_json_str,
                fetched_at=now
            )
            db.add(new_cache)
        db.commit()
        
        release_data = {
            "tag_name": tag_name,
            "name": rel_name,
            "published_at": pub_at,
            "html_url": html_url,
            "body": body,
            "assets": raw_assets,
            "fetched_at": now
        }

    # 执行一次本地已缓存文件过期清理
    cleanup_expired_and_oversized_cache(db)
    
    # 查询当前客户端在本地 downloads 目录已缓存的文件
    cached_downloads = db.query(ClientDownload).filter(
        ClientDownload.client_name == client_id
    ).all()
    
    # 按 asset_id 或 filename 构建索引
    cached_map = {}
    for cd in cached_downloads:
        remaining_seconds = int((cd.cached_at + timedelta(hours=CACHE_EXPIRE_HOURS) - now).total_seconds())
        if remaining_seconds > 0:
            if cd.asset_id:
                cached_map[str(cd.asset_id)] = (cd.filename, remaining_seconds)
            cached_map[cd.filename] = (cd.filename, remaining_seconds)

    # 格式化组装最终 Assets 列表（确保仅返回合法的安装包文件）
    formatted_assets = []
    for asset in release_data.get("assets", []):
        aname = asset.get("name", "")
        # 双重校验安装包格式
        if not is_valid_installer_asset(aname):
            continue
            
        aid = str(asset.get("id"))
        asize = asset.get("size", 0)
        adurl = asset.get("download_url")
        
        is_cached = False
        cached_fn = None
        cached_exp = None
        
        # 匹配缓存
        if aid in cached_map:
            is_cached = True
            cached_fn, cached_exp = cached_map[aid]
        else:
            # 尝试根据文件名匹配
            for key, val in cached_map.items():
                if aname in key or key == aname:
                    is_cached = True
                    cached_fn, cached_exp = val
                    break
        
        formatted_assets.append({
            "id": aid,
            "name": aname,
            "size": asize,
            "size_human": format_file_size(asize),
            "download_url": adurl,
            "download_count": asset.get("download_count", 0),
            "is_cached": is_cached,
            "cached_filename": cached_fn,
            "cached_expires_in": cached_exp
        })

    return {
        "client_id": client_id,
        "client_name": meta["name"],
        "repo": meta["repo"],
        "tag_name": release_data.get("tag_name"),
        "release_name": release_data.get("name"),
        "published_at": release_data.get("published_at"),
        "html_url": release_data.get("html_url"),
        "body": release_data.get("body"),
        "assets": formatted_assets,
        "from_cache": use_local_cache,
        "cache_fetched_at": release_data.get("fetched_at")
    }

# =========================================================================
# 3. 异步下载任务管理器 (DownloadTaskManager)
# =========================================================================

class DownloadTaskManager:
    """
    内存下载任务管理器
    
    作用：
        管理正在执行的从 GitHub 到 NodeHarbor 服务器的流式下载任务，
        记录实时已下载字节数、下载速度、完成度百分比，并支持前端进度轮询。
    """
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取指定任务状态"""
        return self.tasks.get(task_id)

    def create_task(self, client_id: str, asset_id: str, asset_name: str, download_url: str, version: str) -> str:
        """创建新的下载任务"""
        task_id = uuid.uuid4().hex
        self.tasks[task_id] = {
            "task_id": task_id,
            "client_id": client_id,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "download_url": download_url,
            "version": version,
            "status": "pending",           # pending, downloading, completed, failed
            "progress": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed_human": "0 B/s",
            "filename": None,
            "error": None,
            "created_at": time.time()
        }
        return task_id

    async def run_download(self, task_id: str):
        """
        在后台异步执行文件流式下载，实时更新任务状态与进度
        """
        task = self.tasks.get(task_id)
        if not task:
            return

        client_id = task["client_id"]
        asset_id = str(task["asset_id"])
        asset_name = task["asset_name"]
        download_url = task["download_url"]
        version = task["version"]

        task["status"] = "downloading"
        os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
        
        # 构造安全且规范的存储文件名
        safe_name = os.path.basename(asset_name)
        final_filename = f"{client_id}_{version}_{safe_name}"
        final_file_path = os.path.join(settings.DOWNLOAD_DIR, final_filename)
        tmp_filename = f"{final_filename}.{task_id[:8]}.tmp"
        tmp_file_path = os.path.join(settings.DOWNLOAD_DIR, tmp_filename)

        # 检查是否此前已有相同的缓存
        db = SessionLocal()
        try:
            cleanup_expired_and_oversized_cache(db)
            existing = db.query(ClientDownload).filter(
                ClientDownload.client_name == client_id,
                ClientDownload.filename == final_filename
            ).first()
            if existing and os.path.exists(final_file_path):
                existing.cached_at = datetime.utcnow()
                db.commit()
                task["status"] = "completed"
                task["progress"] = 100.0
                task["filename"] = final_filename
                return
        finally:
            db.close()

        # 开始从 GitHub 下载
        try:
            headers = {
                "User-Agent": "NodeHarbor-ProxyClientManager/1.0"
            }
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, headers=headers, timeout=aiohttp.ClientTimeout(total=600)) as response:
                    if response.status != 200:
                        raise Exception(f"GitHub 返回 HTTP {response.status}")

                    total_size = int(response.headers.get("content-length", 0))
                    task["total_bytes"] = total_size

                    downloaded = 0
                    last_time = time.time()
                    last_downloaded = 0

                    async with aiofiles.open(tmp_file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(128 * 1024):  # 128KB 块
                            if not chunk:
                                break
                            await f.write(chunk)
                            downloaded += len(chunk)
                            task["downloaded_bytes"] = downloaded

                            # 计算进度与瞬时速度
                            now_time = time.time()
                            time_diff = now_time - last_time
                            if time_diff >= 0.5:
                                bytes_diff = downloaded - last_downloaded
                                speed = bytes_diff / time_diff
                                task["speed_human"] = f"{format_file_size(int(speed))}/s"
                                if total_size > 0:
                                    task["progress"] = round(min((downloaded / total_size) * 100, 99.9), 1)
                                last_time = now_time
                                last_downloaded = downloaded

            # 下载完成，重命名临时文件为最终文件
            if os.path.exists(final_file_path):
                delete_file(final_file_path)
            os.rename(tmp_file_path, final_file_path)

            file_actual_size = os.path.getsize(final_file_path)

            # 保存入数据库记录
            db = SessionLocal()
            try:
                # 检查缓存是否超过 512MB 限制
                cleanup_expired_and_oversized_cache(db)
                
                # 如果原本有记录则更新，无则新增
                rec = db.query(ClientDownload).filter(
                    ClientDownload.client_name == client_id,
                    ClientDownload.filename == final_filename
                ).first()
                
                if rec:
                    rec.file_size = file_actual_size
                    rec.cached_at = datetime.utcnow()
                    rec.asset_id = asset_id
                    rec.download_url = download_url
                    rec.version = version
                else:
                    new_rec = ClientDownload(
                        client_name=client_id,
                        asset_id=asset_id,
                        platform="all",
                        version=version,
                        filename=final_filename,
                        file_size=file_actual_size,
                        download_url=download_url,
                        cached_at=datetime.utcnow()
                    )
                    db.add(new_rec)
                db.commit()
            finally:
                db.close()

            task["status"] = "completed"
            task["progress"] = 100.0
            task["filename"] = final_filename
            task["speed_human"] = "0 B/s"

        except Exception as e:
            delete_file(tmp_file_path)
            task["status"] = "failed"
            task["error"] = str(e)
            task["speed_human"] = "0 B/s"

# 全局任务管理器实例
download_manager = DownloadTaskManager()

# =========================================================================
# 4. 获取已缓存文件物理路径
# =========================================================================

def get_cached_file_path(db: Session, client_id: str, filename: str) -> str:
    """
    根据客户端标识和文件名/资产标识，获取服务器本地未过期的缓存文件绝对路径。
    
    多重智能匹配策略：
        1. 精确匹配数据库 ClientDownload.filename == safe_filename；
        2. 匹配 ClientDownload.asset_id == safe_filename；
        3. 匹配 ClientDownload.filename 以 safe_filename 结尾 (兼容传入原始未加前缀的文件名)；
        4. 若数据库未查到但磁盘 downloads/ 目录下存在匹配文件，自动补全新记录并返回路径。
    
    参数:
        db: SQLAlchemy 会话
        client_id: 客户端标识
        filename: 缓存文件名或原始安装包名
    返回:
        物理文件绝对路径
    """
    cleanup_expired_and_oversized_cache(db)
    
    client_id = client_id.lower()
    safe_filename = os.path.basename(filename).strip()
    
    # 策略 1: 精确匹配存储文件名
    record = db.query(ClientDownload).filter(
        ClientDownload.client_name == client_id,
        ClientDownload.filename == safe_filename
    ).first()
    
    # 策略 2: 匹配 asset_id
    if not record:
        record = db.query(ClientDownload).filter(
            ClientDownload.client_name == client_id,
            ClientDownload.asset_id == safe_filename
        ).first()

    # 策略 3: 匹配原始文件名结尾 (如传入 v2rayN-With-Core.zip 匹配 v2rayn_7.24.4_v2rayN-With-Core.zip)
    if not record:
        all_client_records = db.query(ClientDownload).filter(
            ClientDownload.client_name == client_id
        ).all()
        for r in all_client_records:
            if r.filename == safe_filename or r.filename.endswith(f"_{safe_filename}") or safe_filename in r.filename:
                record = r
                break
    
    if record:
        file_path = os.path.join(settings.DOWNLOAD_DIR, record.filename)
        if os.path.exists(file_path):
            return file_path
        else:
            db.delete(record)
            db.commit()

    # 策略 4: 直接扫描磁盘 downloads 目录下的实际文件
    if os.path.exists(settings.DOWNLOAD_DIR):
        for f in os.listdir(settings.DOWNLOAD_DIR):
            if f.endswith(".tmp"):
                continue
            if f == safe_filename or f.endswith(f"_{safe_filename}") or (f.startswith(client_id) and safe_filename in f):
                target_fp = os.path.join(settings.DOWNLOAD_DIR, f)
                if os.path.isfile(target_fp):
                    return target_fp

    raise HTTPException(status_code=404, detail=f"服务端未找到客户端 {client_id} 的缓存文件: {safe_filename}，请重新缓存")

# =========================================================================
# 5. 后台定时清理任务 Worker (每 60 秒轮询)
# =========================================================================

async def background_cleanup_scheduler():
    """
    后台定时清理循环协程：
    每隔 60 秒自动唤起，扫描并清理超过 1 小时的过期文件，并在总用量超出 512MB 时清空缓存。
    """
    while True:
        try:
            await asyncio.sleep(60)
            db = SessionLocal()
            try:
                cleanup_expired_and_oversized_cache(db)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Scheduled Cleanup Error]: {e}")
            await asyncio.sleep(10)
