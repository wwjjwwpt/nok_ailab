"""
日志管理 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..core.deps import get_current_user, PermissionDependency
from ..models import User, LoginLog, OperationLog

router = APIRouter()


@router.get("/login", response_model=dict, summary="获取登录日志")
async def get_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("log:view")),
):
    """获取登录日志列表"""
    query = db.query(LoginLog)

    if username:
        query = query.filter(LoginLog.username.contains(username))
    if status:
        query = query.filter(LoginLog.login_status == status)

    total = query.count()
    logs = (
        query.order_by(LoginLog.login_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "ip_address": log.ip_address,
                "login_status": log.login_status,
                "fail_reason": log.fail_reason,
                "login_time": log.login_time.isoformat() if log.login_time else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": total > page * page_size,
    }


@router.get("/operation", response_model=dict, summary="获取操作日志")
async def get_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependency("log:view")),
):
    """获取操作日志列表"""
    query = db.query(OperationLog)

    if username:
        query = query.filter(OperationLog.username.contains(username))
    if module:
        query = query.filter(OperationLog.module.contains(module))
    if status:
        query = query.filter(OperationLog.status == status)

    total = query.count()
    logs = (
        query.order_by(OperationLog.operation_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "module": log.module,
                "operation": log.operation,
                "method": log.method,
                "request_url": log.request_url,
                "ip_address": log.ip_address,
                "duration_ms": log.duration_ms,
                "status": log.status,
                "error_msg": log.error_msg,
                "operation_time": log.operation_time.isoformat()
                if log.operation_time
                else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": total > page * page_size,
    }
