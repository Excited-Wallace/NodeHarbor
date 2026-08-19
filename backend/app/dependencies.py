"""
NodeHarbor 依赖项注入模块 (dependencies.py)

文件作用：
    提供 FastAPI 路由所依赖的权限认证和用户校验依赖项。
    支持从 HTTP Authorization Header (Bearer Token) 或 URL Query 参数 (?token=...) 中解析 JWT Token，
    以同时满足常规 API 调用与浏览器文件直接下载、大文件流式传输等场景的鉴权需求。

包含的依赖函数：
    1. get_current_user: 校验 Token 并返回当前登录用户对象
    2. require_admin: 校验当前用户是否具备管理员 (admin) 权限
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.config import settings
from app.models import User
from app.auth import ALGORITHM

# 配置 HTTPBearer 且设置 auto_error=False，以便兼容 Header 与 URL Query 两种传参方式
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_query: Optional[str] = Query(None, alias="token", description="URL Query 中的访问令牌"),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前请求的用户身份
    
    认证逻辑：
        1. 优先从 Authorization: Bearer <token> 请求头中提取 Token；
        2. 若请求头未携带，则尝试从 URL Query 中的 token 参数提取（支持浏览器直连文件下载）；
        3. 解析 JWT Payload 并验证签名，查询数据库返回 User 模型；
        4. 若验证失败或用户不存在，抛出 401 Unauthorized。
    """
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif token_query:
        token = token_query

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证凭据无效或已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    校验当前登录用户是否具有管理员权限
    
    规则：
        若用户角色不是 'admin'，抛出 403 Forbidden 权限不足异常。
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，该操作仅限系统管理员执行",
        )
    return current_user
