"""
NodeHarbor 后端主应用入口 (main.py)

文件作用：
    FastAPI 应用程序的初始化与配置中心。
    负责注册跨域中间件 (CORS)、挂载各业务路由模块、管理应用生命周期 (数据库表初始化、默认账号生成以及客户端缓存后台定时清理任务启动与取消)。

挂载的路由模块：
    1. /api/auth    - 用户认证与登录
    2. /api/configs - 订阅配置管理与公开订阅
    3. /api/clients - 代理客户端卡片、GitHub Release 抓取与中转缓存下载
    4. /api/system  - 系统资源与监控状态
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, configs, clients, system
from app.database import engine, SessionLocal
from app.models import Base
from app.services.auth_service import init_default_users
from app.services.client_service import background_cleanup_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用程序生命周期管理器
    
    启动流程：
        1. 自动根据 models 创建所有尚未建立的数据库表结构；
        2. 初始化系统默认管理员与普通用户账号；
        3. 启动后台异步定时任务，每隔 60 秒轮询清理超过 1 小时的缓存文件并在总缓存超过 512MB 时自动清空。
    
    关闭流程：
        取消并等待后台定时清理任务安全退出。
    """
    # 1. 确保所有数据库表结构已创建
    Base.metadata.create_all(bind=engine)
    
    # 2. 初始化默认用户
    db = SessionLocal()
    try:
        init_default_users(db)
    finally:
        db.close()
        
    # 3. 启动客户端安装包缓存定时清理后台任务
    cleanup_task = asyncio.create_task(background_cleanup_scheduler())
    
    yield
    
    # 应用程序关闭时取消后台任务
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# 实例化 FastAPI 应用
app = FastAPI(
    title="NodeHarbor API",
    description="NodeHarbor 代理订阅管理与多平台客户端聚合下载分发系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS 跨域支持，允许前端所有来源访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载各模块业务路由
app.include_router(auth.router)
app.include_router(configs.router)
app.include_router(clients.router)
app.include_router(system.router)

@app.get("/")
def root():
    """
    根健康检查接口
    """
    return {
        "app": "NodeHarbor API",
        "status": "running",
        "version": "1.0.0"
    }
