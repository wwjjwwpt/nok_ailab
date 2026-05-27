"""
权限管理 API 路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..core.database import get_db
from ..schemas import PermissionCreate, PermissionUpdate
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, Permission, Menu, PermissionMenu

router = APIRouter()


@router.get("", response_model=List[dict], summary="获取权限列表")
async def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:manage")),
):
    """获取权限列表"""
    permissions = db.query(Permission).order_by(Permission.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
            "menu_ids": [pm.menu_id for pm in db.query(PermissionMenu).filter(PermissionMenu.permission_id == p.id).all()],
        }
        for p in permissions
    ]


@router.get("/{perm_id}", response_model=dict, summary="获取权限详情")
async def get_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:manage")),
):
    permission = db.query(Permission).filter(Permission.id == perm_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    menu_ids = [pm.menu_id for pm in db.query(PermissionMenu).filter(PermissionMenu.permission_id == perm_id).all()]

    return {
        "id": permission.id,
        "name": permission.name,
        "code": permission.code,
        "description": permission.description,
        "menu_ids": menu_ids,
    }


@router.post("", response_model=dict, summary="创建权限")
async def create_permission(
    perm_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:add")),
):
    """创建新权限"""
    # 检查权限编码是否已存在
    existing = db.query(Permission).filter(Permission.code == perm_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="权限编码已存在")

    permission = Permission(
        name=perm_data.name,
        code=perm_data.code,
        description=perm_data.description,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)

    # 绑定菜单
    if perm_data.menu_ids:
        for menu_id in perm_data.menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise HTTPException(status_code=404, detail=f"菜单 ID={menu_id} 不存在")
            perm_menu = PermissionMenu(permission_id=permission.id, menu_id=menu_id)
            db.add(perm_menu)
        db.commit()

    return {"message": "权限创建成功", "data": {"permission_id": permission.id}}


@router.put("/{perm_id}", response_model=dict, summary="更新权限")
async def update_permission(
    perm_id: int,
    perm_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:edit")),
):
    """更新权限信息"""
    permission = db.query(Permission).filter(Permission.id == perm_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    # 更新基本信息
    permission.name = perm_data.name
    permission.code = perm_data.code
    permission.description = perm_data.description

    # 更新绑定的菜单（先删除旧的，再添加新的）
    if perm_data.menu_ids is not None:
        db.query(PermissionMenu).filter(PermissionMenu.permission_id == perm_id).delete()
        for menu_id in perm_data.menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if menu:
                perm_menu = PermissionMenu(permission_id=perm_id, menu_id=menu_id)
                db.add(perm_menu)
        db.commit()

    db.commit()

    return {"message": "权限更新成功"}


@router.delete("/{perm_id}", response_model=dict, summary="删除权限")
async def delete_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:delete")),
):
    """删除权限"""
    permission = db.query(Permission).filter(Permission.id == perm_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    # 先删除关联的菜单绑定
    db.query(PermissionMenu).filter(PermissionMenu.permission_id == perm_id).delete()
    db.delete(permission)
    db.commit()

    return {"message": "权限删除成功"}


@router.get("/menu/{menu_id}/permissions", response_model=List[dict], summary="获取菜单关联的权限")
async def get_menu_permissions(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("permission:manage")),
):
    """获取指定菜单关联的所有权限"""
    perm_ids = [pm.permission_id for pm in db.query(PermissionMenu).filter(PermissionMenu.menu_id == menu_id).all()]
    permissions = db.query(Permission).filter(Permission.id.in_(perm_ids)).all() if perm_ids else []
    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
        }
        for p in permissions
    ]
