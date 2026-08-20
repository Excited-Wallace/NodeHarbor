from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.dependencies import require_admin
from app.models import User, Config, ClientDownload
from app.schemas import SystemStatusResponse
from app.config import settings

router = APIRouter(prefix="/api/system", tags=["system"])

def get_dir_size(path: str) -> int:
    """计算目录大小"""
    total = 0
    if os.path.exists(path):
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
    return total

@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    供管理员查看系统状态信息
    """
    configs_count = db.query(Config).count()
    cached_clients_count = db.query(ClientDownload).count()
    users_count = db.query(User).count()
    
    db_path = os.path.join(settings.DATA_DIR, "nodeharbor.db")
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    downloads_size = get_dir_size(settings.DOWNLOAD_DIR)
    
    return {
        "database_size": db_size,
        "configs_count": configs_count,
        "downloads_size": downloads_size,
        "cached_clients_count": cached_clients_count,
        "users_count": users_count
    }
