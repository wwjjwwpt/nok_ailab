"""
菜单管理 API 路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from ..core.database import get_db
from ..schemas import MenuCreate, MenuUpdate, MenuResponse
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, Menu, Permission, PermissionMenu

router = APIRouter()


@router.get("/tree", response_model=List[dict], summary="获取菜单树")
async def get_menu_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户可访问的菜单树
    前端可根据此数据动态生成导航菜单
    """
    from ..services.permission_service import PermissionService

    permission_service = PermissionService(db)
    menus = await permission_service.get_user_menus(current_user.id)

    return menus


@router.get("", response_model=List[MenuResponse], summary="获取所有菜单")
async def get_all_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:manage")),
):
    """获取所有菜单 (管理后台使用)"""
    menus = db.query(Menu).order_by(Menu.sort_order, Menu.id).all()

    # 构建树形结构
    def build_tree(menus: List[Menu]) -> List[dict]:
        menu_dict = {m.id: {**vars(m), "children": []} for m in menus}
        result = []
        for m in menus:
            if m.parent_id == 0 or m.parent_id not in menu_dict:
                result.append(menu_dict[m.id])
            else:
                menu_dict[m.parent_id]["children"].append(menu_dict[m.id])
        return result

    return build_tree(menus)


@router.get("/{menu_id}", response_model=MenuResponse, summary="获取菜单详情")
async def get_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return menu


@router.post("", response_model=dict, summary="创建菜单")
async def create_menu(
    menu_data: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:add")),
):
    """创建新菜单"""
    existing = db.query(Menu).filter(Menu.code == menu_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="菜单编码已存在")

    menu = Menu(**menu_data.model_dump())
    db.add(menu)
    db.commit()
    db.refresh(menu)

    return {"message": "菜单创建成功", "data": {"menu_id": menu.id}}


@router.put("/{menu_id}", response_model=dict, summary="更新菜单")
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:edit")),
):
    """更新菜单信息"""
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    update_data = menu_data.model_dump(exclude={"id"})
    for key, value in update_data.items():
        setattr(menu, key, value)

    db.commit()
    db.refresh(menu)

    return {"message": "菜单更新成功"}


@router.delete("/{menu_id}", response_model=dict, summary="删除菜单")
async def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:delete")),
):
    """删除菜单"""
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    # 检查是否有子菜单
    children = db.query(Menu).filter(Menu.parent_id == menu_id).first()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子菜单")

    db.delete(menu)
    db.commit()

    return {"message": "菜单删除成功"}


@router.get("/{menu_id}/permissions", response_model=List[dict], summary="获取菜单绑定的权限")
async def get_menu_permissions(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:manage")),
):
    """获取指定菜单绑定的所有权限"""
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    # 通过 permission_menus 表获取绑定的权限
    perm_menu_records = db.query(PermissionMenu).filter(PermissionMenu.menu_id == menu_id).all()
    perm_ids = [pm.permission_id for pm in perm_menu_records]
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


@router.post("/{menu_id}/permissions", response_model=dict, summary="给菜单绑定权限")
async def bind_menu_permissions(
    menu_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("menu:manage")),
):
    """给菜单绑定权限（覆盖式绑定）"""
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    # 验证权限是否存在
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(permissions) != len(permission_ids):
        raise HTTPException(status_code=404, detail="存在不存在的权限 ID")

    # 删除旧的绑定
    db.query(PermissionMenu).filter(PermissionMenu.menu_id == menu_id).delete()

    # 添加新的绑定
    for perm_id in permission_ids:
        perm_menu = PermissionMenu(menu_id=menu_id, permission_id=perm_id)
        db.add(perm_menu)

    db.commit()

    return {"message": "权限绑定成功"}
