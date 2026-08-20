"""
NodeHarbor 用户管理业务逻辑层 (user_service.py)

文件作用：
    提供系统用户的全生命周期管理业务逻辑，包括：
    - 查询系统中所有注册用户（管理员与普通用户）；
    - 管理员创建新用户（包含用户名唯一性检查与 bcrypt 密码哈希加密）；
    - 管理员编辑用户信息（重置/修改密码、切换角色），并进行核心安全边界保护；
    - 管理员删除用户，执行防误删自身与防删除唯一管理员的强校验。

安全保护规则：
    1. 禁止管理员删除当前正处于登录状态的自身账号；
    2. 当系统中仅剩最后 1 个管理员账号时，禁止删除该管理员或将其角色降级为普通用户；
    3. 所有密码均采用 bcrypt 单向哈希算法加密后写入数据库，严禁明文存储。
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.auth import get_password_hash


def get_all_users(db: Session) -> List[User]:
    """
    获取系统中所有用户的列表
    
    函数作用：
        查询并返回全部用户实体，按创建时间正序排列。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        
    返回值：
        List[User]: 用户模型实例列表
    """
    return db.query(User).order_by(User.id.asc()).all()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    根据用户 ID 查询指定用户
    
    函数作用：
        通过主键 ID 查询用户详情，若不存在则返回 None。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        user_id: 用户主键 ID
        
    返回值：
        Optional[User]: 查询到的 User 实例，或 None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    根据用户名查询用户
    
    函数作用：
        查询指定账号名的用户，用于注册或新增时的重名校验。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        username: 待查询的用户名
        
    返回值：
        Optional[User]: 查询到的 User 实例，或 None
    """
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, data: UserCreate) -> User:
    """
    管理员创建新用户账号
    
    函数作用：
        1. 检查用户名是否已被占用，若已存在则抛出 400 错误；
        2. 校验角色合法性（仅允许 'admin' 或 'user'）；
        3. 对明文密码使用 bcrypt 进行单向哈希加密；
        4. 实例化 User 模型写入数据库并提交事务。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        data: UserCreate 请求数据对象 (username, password, role)
        
    返回值：
        User: 创建成功后的 User 实例
        
    异常：
        HTTPException(400): 用户名已存在或角色不合法
    """
    # 1. 检查用户名唯一性
    existing = get_user_by_username(db, data.username.strip())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户名 '{data.username}' 已被占用，请使用其他用户名"
        )
        
    # 2. 校验角色有效性
    role = data.role.strip().lower()
    if role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户角色无效，仅支持 'admin' (管理员) 或 'user' (普通用户)"
        )
        
    # 3. 密码哈希加密
    hashed_pwd = get_password_hash(data.password)
    
    # 4. 创建并持久化用户
    new_user = User(
        username=data.username.strip(),
        role=role,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(db: Session, user_id: int, data: UserUpdate, current_user: User) -> User:
    """
    管理员修改指定用户的密码或角色权限
    
    函数作用：
        1. 校验目标用户是否存在；
        2. 若修改密码，则重新使用 bcrypt 计算新密码哈希并更新；
        3. 若修改角色，检查是否会造成系统中无管理员的危险（防止唯一管理员降级）；
        4. 保存修改并提交数据库事务。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        user_id: 目标修改的用户主键 ID
        data: UserUpdate 更新数据对象 (password 可选, role 可选)
        current_user: 当前发起操作的管理员用户对象
        
    返回值：
        User: 更新后的 User 实例
        
    异常：
        HTTPException(404): 目标用户不存在
        HTTPException(400): 角色参数非法，或试图将系统中唯一的管理员降级为普通用户
    """
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的用户不存在"
        )
        
    # 1. 如果请求提供了新密码，则哈希加密后更新
    if data.password is not None and len(data.password.strip()) > 0:
        target_user.password_hash = get_password_hash(data.password.strip())
        
    # 2. 如果请求更新了角色
    if data.role is not None:
        target_role = data.role.strip().lower()
        if target_role not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户角色无效，仅支持 'admin' 或 'user'"
            )
            
        # 安全检查：如果目标用户当前是 admin，且试图变更为 user
        if target_user.role == "admin" and target_role == "user":
            # 统计系统中当前的管理员总数
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作失败：系统中至少需要保留一个管理员账号，无法将最后一名管理员降级"
                )
        target_user.role = target_role
        
    db.commit()
    db.refresh(target_user)
    return target_user


def delete_user(db: Session, user_id: int, current_user: User) -> bool:
    """
    管理员删除指定用户
    
    函数作用：
        1. 校验目标用户是否存在；
        2. 安全防护 1：禁止管理员删除当前登录账号自身；
        3. 安全防护 2：禁止删除系统中唯一的管理员账号；
        4. 执行数据库物理删除并提交事务。
        
    参数说明：
        db: SQLAlchemy 数据库会话
        user_id: 待删除的用户主键 ID
        current_user: 当前发起删除操作的管理员用户对象
        
    返回值：
        bool: 删除成功返回 True
        
    异常：
        HTTPException(404): 目标用户不存在
        HTTPException(400): 试图删除自身或试图删除唯一管理员
    """
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的用户不存在"
        )
        
    # 安全防护 1：禁止删除当前登录的自身账号
    if target_user.id == current_user.id or target_user.username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="安全限制：无法删除当前正处于登录状态的自身管理员账号"
        )
        
    # 安全防护 2：禁止删除最后一名管理员
    if target_user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="安全限制：系统中仅剩最后一名管理员，禁止删除该管理员账号"
            )
            
    db.delete(target_user)
    db.commit()
    return True
