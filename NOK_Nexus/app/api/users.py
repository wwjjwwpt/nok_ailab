"""
用户管理 API 路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PageResponse,
)
from ..core.deps import get_current_user, PermissionDependency
from ..models import User

router = APIRouter()


@router.get("", response_model=PageResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: Optional[str] = None,
    email: Optional[str] = None,
    dept_id: Optional[int] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页获取用户列表"""
    query = db.query(User)

    if username:
        query = query.filter(User.username.contains(username))
    if email:
        query = query.filter(User.email.contains(email))
    if dept_id:
        query = query.filter(User.dept_id == dept_id)
    if status is not None:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [user.to_dict() for user in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": total > page * page_size,
    }


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("", response_model=dict, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("user:manage")),
):
    """创建新用户"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    from ..core.security import get_password_hash

    user = User(
        username=user_data.username,
        password=get_password_hash(user_data.password),
        email=user_data.email,
        phone=user_data.phone,
        nickname=user_data.nickname or user_data.username,
        dept_id=user_data.dept_id,
        status=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "用户创建成功", "data": {"user_id": user.id}}


@router.put("/{user_id}", response_model=dict, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("user:manage")),
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        from ..core.security import get_password_hash

        update_data["password"] = get_password_hash(update_data["password"])

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return {"message": "用户更新成功"}


@router.delete("/{user_id}", response_model=dict, summary="删除用户")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("user:manage")),
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()

    return {"message": "用户删除成功"}


@router.post("/{user_id}/roles", response_model=dict, summary="分配角色")
async def assign_user_roles(
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("user:manage")),
):
    """给用户分配角色"""
    from ..models import User as UserModel, Role, UserRole

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证角色存在
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    if len(roles) != len(role_ids):
        raise HTTPException(status_code=404, detail="存在不存在的角色")

    # 删除原有角色关联
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()

    # 添加新角色
    for role_id in role_ids:
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)

    db.commit()

    return {"message": "角色分配成功"}


@router.get("/{user_id}/roles", response_model=List[dict], summary="获取用户角色")
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户的角色列表"""
    from ..models import User as UserModel, UserRole, Role

    user_roles = (
        db.query(UserRole, Role)
        .join(Role, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )

    return [{"id": r[1].id, "name": r[1].name, "code": r[1].code} for r in user_roles]


@router.get("/{user_id}/permissions", response_model=List[dict], summary="获取用户权限")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户的功能权限列表（包括角色继承和直接权限）"""
    from ..services.permission_service import PermissionService
    from ..models import Permission

    permission_service = PermissionService(db)
    perm_codes = await permission_service.get_user_permission_codes(user_id)

    # 获取权限详情
    permissions = db.query(Permission).filter(Permission.code.in_(perm_codes)).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
        }
        for p in permissions
    ]


@router.post("/{user_id}/permissions", response_model=dict, summary="分配直接权限")
async def assign_user_permissions(
    user_id: int,
    permissions: List[dict],  # [{"permission_id": 1, "grant_type": 1}, ...]
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("user:manage")),
):
    """给用户分配直接权限（支持允许/拒绝两种类型）"""
    from ..models import UserPermission, Permission

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证权限存在
    perm_ids = [p["permission_id"] for p in permissions]
    perms = db.query(Permission).filter(Permission.id.in_(perm_ids)).all()
    if len(perms) != len(perm_ids):
        raise HTTPException(status_code=404, detail="存在不存在的权限")

    # 删除原有直接权限
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()

    # 添加新权限
    for perm in permissions:
        user_perm = UserPermission(
            user_id=user_id,
            permission_id=perm["permission_id"],
            grant_type=perm.get("grant_type", 1),  # 1=允许，2=拒绝
        )
        db.add(user_perm)

    db.commit()

    return {"message": "权限分配成功"}
