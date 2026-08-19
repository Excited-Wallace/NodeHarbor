from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, configs, clients, system
from app.database import engine, SessionLocal
from app.models import Base
from app.services.auth_service import init_default_users

app = FastAPI(title="NodeHarbor API")

# 配置 CORS，允许前端的所有请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议指定具体前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(auth.router)
app.include_router(configs.router)
app.include_router(clients.router)
app.include_router(system.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_default_users(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Welcome to NodeHarbor API"}
