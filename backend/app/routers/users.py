"""
NodeHarbor 用户管理路由模块 (routers/users.py)

文件作用：
    提供管理员对系统用户的 CRUD 管理接口，包括：
    - 查询系统内所有用户列表；
    - 创建新用户（可指定角色为管理员或普通用户）；
    - 编辑用户信息（修改密码、修改角色分配）；
    - 删除用户（包含自删保护和唯一管理员保护）。

权限说明：
    所有端点均受到 require_admin 依赖鉴权保护，仅限具有 'admin' 角色的管理员访问。
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas import UserResponse, UserCreate, UserUpdate
from app.services import user_service

# 实例化 APIRouter，设置公共前缀与 Swagger 分组标签
router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    接口：获取系统中所有注册用户列表
    
    调用权限：
        系统管理员 (admin)
        
    请求方法：
        GET /api/users
        Header: Authorization: Bearer <admin_token>
        
    返回：
        List[UserResponse]: 用户对象数组，包含 id, username, role, created_at
    """
    return user_service.get_all_users(db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    接口：管理员新增用户账号
    
    调用权限：
        系统管理员 (admin)
        
    请求方法：
        POST /api/users
        Header: Authorization: Bearer <admin_token>
        Body (JSON):
            {
                "username": "new_user",
                "password": "secret_password",
                "role": "user"  # 或 "admin"
            }
            
    返回：
        UserResponse: 新创建成功的用户对象
    """
    return user_service.create_user(db, data)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    接口：管理员修改指定用户的密码或角色权限
    
    调用权限：
        系统管理员 (admin)
        
    请求方法：
        PUT /api/users/{user_id}
        Header: Authorization: Bearer <admin_token>
        Body (JSON):
            {
                "password": "new_password", # 可选，若不修改密码则无需传递或为 null
                "role": "admin"            # 可选，若不修改角色则无需传递或为 null
            }
            
    返回：
        UserResponse: 更新后的用户对象
    """
    return user_service.update_user(
        db=db,
        user_id=user_id,
        data=data,
        current_user=current_user
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    接口：管理员删除指定用户
    
    调用权限：
        系统管理员 (admin)
        
    请求方法：
        DELETE /api/users/{user_id}
        Header: Authorization: Bearer <admin_token>
        
    返回：
        JSON: {"status": "success", "message": "用户已成功删除"}
    """
    user_service.delete_user(
        db=db,
        user_id=user_id,
        current_user=current_user
    )
    return {
        "status": "success",
        "message": "用户已成功删除"
    }
