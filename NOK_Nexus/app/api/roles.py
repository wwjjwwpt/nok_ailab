"""
角色管理 API 路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..core.database import get_db
from ..schemas import RoleCreate, RoleUpdate, RoleResponse
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, Role, RoleHierarchy, RolePermission, Permission, RoleMenu, Menu

router = APIRouter()


@router.get("", response_model=List[RoleResponse], summary="获取角色列表")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有角色"""
    roles = db.query(Role).order_by(Role.id).all()
    return roles


@router.get("/{role_id}", response_model=RoleResponse, summary="获取角色详情")
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.post("", response_model=dict, summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:add")),
):
    """创建新角色"""
    # 检查角色编码是否已存在
    existing = db.query(Role).filter(Role.code == role_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role = Role(
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
        is_system=False,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    # 分配权限
    if role_data.permission_ids:
        for perm_id in role_data.permission_ids:
            role_perm = RolePermission(role_id=role.id, permission_id=perm_id)
            db.add(role_perm)
        db.commit()

    return {"message": "角色创建成功", "data": {"role_id": role.id}}


@router.put("/{role_id}", response_model=dict, summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:edit")),
):
    """更新角色信息"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=403, detail="系统内置角色不可修改")

    # 更新字段
    role.name = role_data.name
    role.code = role_data.code
    role.description = role_data.description

    db.commit()
    db.refresh(role)

    return {"message": "角色更新成功"}


@router.delete("/{role_id}", response_model=dict, summary="删除角色")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:delete")),
):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=403, detail="系统内置角色不可删除")

    db.delete(role)
    db.commit()

    return {"message": "角色删除成功"}


@router.get("/{role_id}/permissions", response_model=List[dict], summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色的权限列表（包含继承的权限）"""
    from sqlalchemy.orm import joinedload

    # 获取角色直接权限
    role_perms = (
        db.query(RolePermission)
        .join(Permission)
        .options(joinedload(RolePermission.permission))
        .filter(RolePermission.role_id == role_id)
        .all()
    )

    # 获取子角色（该角色作为父角色时继承的权限）
    child_role_ids = (
        db.query(RoleHierarchy.child_role_id)
        .filter(RoleHierarchy.parent_role_id == role_id, RoleHierarchy.status == 1)
        .all()
    )
    child_ids = [c[0] for c in child_role_ids]

    inherited_perms = []
    if child_ids:
        inherited_perms = (
            db.query(RolePermission)
            .join(Permission)
            .options(joinedload(RolePermission.permission))
            .filter(RolePermission.role_id.in_(child_ids))
            .all()
        )

    # 合并权限（去重）
    seen = set()
    result = []
    for rp in role_perms + inherited_perms:
        if rp.permission_id not in seen:
            seen.add(rp.permission_id)
            result.append({
                "id": rp.permission.id,
                "name": rp.permission.name,
                "code": rp.permission.code,
                "description": rp.permission.description,
                "inherited_from": role_id if rp in role_perms else None
            })

    return result


@router.post("/{role_id}/permissions", response_model=dict, summary="分配角色权限")
async def assign_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:edit")),
):
    """给角色分配权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证权限存在
    perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(perms) != len(permission_ids):
        raise HTTPException(status_code=404, detail="存在不存在的权限")

    # 删除原有权限
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    # 添加新权限
    for perm_id in permission_ids:
        role_perm = RolePermission(role_id=role_id, permission_id=perm_id)
        db.add(role_perm)

    db.commit()

    return {"message": "权限分配成功"}


# ==================== 角色层级管理 ====================

@router.get("/{role_id}/hierarchy", response_model=Dict[str, Any], summary="获取角色层级关系")
async def get_role_hierarchy(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色的层级关系（父角色和子角色）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取父角色（该角色作为子角色时的父角色）
    parent_relations = (
        db.query(RoleHierarchy, Role)
        .join(Role, RoleHierarchy.parent_role_id == Role.id)
        .filter(RoleHierarchy.child_role_id == role_id, RoleHierarchy.status == 1)
        .all()
    )
    parent_roles = [
        {"id": r.id, "name": r.name, "code": r.code}
        for _, r in parent_relations
    ]

    # 获取子角色（该角色作为父角色时的子角色）
    child_relations = (
        db.query(RoleHierarchy, Role)
        .join(Role, RoleHierarchy.child_role_id == Role.id)
        .filter(RoleHierarchy.parent_role_id == role_id, RoleHierarchy.status == 1)
        .all()
    )
    child_roles = [
        {"id": r.id, "name": r.name, "code": r.code}
        for _, r in child_relations
    ]

    return {
        "role_id": role_id,
        "role_name": role.name,
        "parent_roles": parent_roles,
        "child_roles": child_roles,
    }


@router.post("/{role_id}/hierarchy/children", response_model=dict, summary="添加子角色")
async def add_child_role(
    role_id: int,
    child_role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:edit")),
):
    """添加子角色（父角色继承子角色的权限）"""
    parent_role = db.query(Role).filter(Role.id == role_id).first()
    child_role = db.query(Role).filter(Role.id == child_role_id).first()

    if not parent_role or not child_role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if parent_role.id == child_role.id:
        raise HTTPException(status_code=400, detail="不能将自己设为子角色")

    # 检查是否已存在
    existing = db.query(RoleHierarchy).filter(
        RoleHierarchy.parent_role_id == role_id,
        RoleHierarchy.child_role_id == child_role_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该层级关系已存在")

    # 检查循环继承
    def check_cycle(parent_id, child_id, visited=None):
        if visited is None:
            visited = set()
        if child_id == parent_id:
            return True
        if child_id in visited:
            return False
        visited.add(child_id)
        # 检查 child 的父角色
        parents = db.query(RoleHierarchy.parent_role_id).filter(
            RoleHierarchy.child_role_id == child_id
        ).all()
        for p in parents:
            if check_cycle(parent_id, p[0], visited):
                return True
        return False

    if check_cycle(role_id, child_role_id):
        raise HTTPException(status_code=400, detail="存在循环继承关系")

    hierarchy = RoleHierarchy(
        parent_role_id=role_id,
        child_role_id=child_role_id,
        status=1
    )
    db.add(hierarchy)
    db.commit()

    return {"message": "子角色添加成功"}


@router.delete("/{role_id}/hierarchy/children/{child_role_id}", response_model=dict, summary="移除子角色")
async def remove_child_role(
    role_id: int,
    child_role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("role:edit")),
):
    """移除子角色关系"""
    existing = db.query(RoleHierarchy).filter(
        RoleHierarchy.parent_role_id == role_id,
        RoleHierarchy.child_role_id == child_role_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="层级关系不存在")

    db.delete(existing)
    db.commit()

    return {"message": "层级关系已移除"}


@router.get("/{role_id}/menus", response_model=List[dict], summary="获取角色菜单")
async def get_role_menus(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色的菜单列表（包含继承的菜单）"""
    # 获取角色 ID 列表（包括子角色）
    child_role_ids = (
        db.query(RoleHierarchy.child_role_id)
        .filter(RoleHierarchy.parent_role_id == role_id, RoleHierarchy.status == 1)
        .all()
    )
    all_role_ids = [role_id] + [c[0] for c in child_role_ids]

    # 查询菜单
    menus = (
        db.query(RoleMenu)
        .join(Menu)
        .filter(RoleMenu.role_id.in_(all_role_ids))
        .all()
    )

    # 去重
    seen = set()
    result = []
    for rm in menus:
        if rm.menu_id not in seen:
            seen.add(rm.menu_id)
            result.append({
                "id": rm.menu.id,
                "name": rm.menu.name,
                "code": rm.menu.code,
                "parent_id": rm.menu.parent_id,
                "path": rm.menu.path,
                "component": rm.menu.component,
                "icon": rm.menu.icon,
                "type": rm.menu.type,
            })

    return result
