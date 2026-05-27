"""
数据权限管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..schemas import DataScopeCreate, DataScopeUpdate
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, DataScope

router = APIRouter()


@router.get("", response_model=List[dict], summary="获取数据权限列表")
async def get_data_scopes(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("data_scope:view")),
):
    """获取所有数据权限规则"""
    scopes = db.query(DataScope).order_by(DataScope.id).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "scope_type": s.scope_type,
            "scope_config": s.scope_config,
            "description": s.description,
        }
        for s in scopes
    ]


@router.post("", response_model=dict, summary="创建数据权限")
async def create_data_scope(
    scope_data: DataScopeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("data_scope:add")),
):
    """创建数据权限规则"""
    existing = db.query(DataScope).filter(DataScope.code == scope_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="数据权限编码已存在")

    scope = DataScope(**scope_data.model_dump())
    db.add(scope)
    db.commit()
    db.refresh(scope)

    return {"message": "数据权限创建成功", "data": {"scope_id": scope.id}}


@router.put("/{scope_id}", response_model=dict, summary="更新数据权限")
async def update_data_scope(
    scope_id: int,
    scope_data: DataScopeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("data_scope:edit")),
):
    """更新数据权限规则"""
    scope = db.query(DataScope).filter(DataScope.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="数据权限不存在")

    update_data = scope_data.model_dump(exclude={"id"})
    for key, value in update_data.items():
        setattr(scope, key, value)

    db.commit()
    db.refresh(scope)

    return {"message": "数据权限更新成功"}


@router.delete("/{scope_id}", response_model=dict, summary="删除数据权限")
async def delete_data_scope(
    scope_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("data_scope:delete")),
):
    """删除数据权限规则"""
    scope = db.query(DataScope).filter(DataScope.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="数据权限不存在")

    db.delete(scope)
    db.commit()

    return {"message": "数据权限删除成功"}
