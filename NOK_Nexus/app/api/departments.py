"""
部门管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..schemas import DepartmentCreate, DepartmentUpdate
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, Department

router = APIRouter()


@router.get("/tree", response_model=List[dict], summary="获取部门树")
async def get_department_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部门树形结构"""
    depts = db.query(Department).order_by(Department.sort_order, Department.id).all()

    def build_tree(depts: List[Department]) -> List[dict]:
        dept_dict = {}
        for d in depts:
            dept_dict[d.id] = {
                "id": d.id,
                "name": d.name,
                "parent_id": d.parent_id,
                "leader_name": d.leader_name,
                "phone": d.phone,
                "email": d.email,
                "sort_order": d.sort_order,
                "full_path": d.full_path,
                "children": []
            }
        result = []
        for d in depts:
            if d.parent_id == 0 or d.parent_id not in dept_dict:
                result.append(dept_dict[d.id])
            else:
                dept_dict[d.parent_id]["children"].append(dept_dict[d.id])
        return result

    return build_tree(depts)


@router.get("", response_model=List[dict], summary="获取部门列表")
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有部门"""
    depts = db.query(Department).order_by(Department.sort_order, Department.id).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "parent_id": d.parent_id,
            "leader_name": d.leader_name,
            "phone": d.phone,
            "email": d.email,
            "sort_order": d.sort_order,
            "full_path": d.full_path,
        }
        for d in depts
    ]


@router.post("", response_model=dict, summary="创建部门")
async def create_department(
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("dept:add")),
):
    """创建新部门"""
    dept = Department(**dept_data.model_dump())

    # 构建完整路径
    if dept.parent_id > 0:
        parent = db.query(Department).filter(Department.id == dept.parent_id).first()
        if parent:
            dept.full_path = f"{parent.full_path}{dept.id}/"
        else:
            dept.full_path = f"/{dept.id}/"
    else:
        dept.full_path = f"/{dept.id}/"

    db.add(dept)
    db.commit()
    db.refresh(dept)

    return {"message": "部门创建成功", "data": {"dept_id": dept.id}}


@router.put("/{dept_id}", response_model=dict, summary="更新部门")
async def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("dept:edit")),
):
    """更新部门信息"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    update_data = dept_data.model_dump(exclude={"id"})
    for key, value in update_data.items():
        setattr(dept, key, value)

    db.commit()
    db.refresh(dept)

    return {"message": "部门更新成功"}


@router.delete("/{dept_id}", response_model=dict, summary="删除部门")
async def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("dept:delete")),
):
    """删除部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 检查是否有子部门
    children = db.query(Department).filter(Department.parent_id == dept_id).first()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子部门")

    db.delete(dept)
    db.commit()

    return {"message": "部门删除成功"}
