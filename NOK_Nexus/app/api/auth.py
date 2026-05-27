"""
认证 API 路由
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from ..core.database import get_db
from ..schemas import (
    UserLogin,
    UserRegister,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    SendVerifyCodeRequest,
    VerifyCodeRequest,
    ResponseBase,
)
from ..services.auth_service import AuthService
from ..core.deps import get_current_user
from ..models import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    用户登录

    - **username**: 用户名/邮箱/手机号
    - **password**: 密码
    - **verify_code**: 验证码 (如果需要)
    """
    auth_service = AuthService(db)
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")

    user, token_data = await auth_service.login(
        login_data, ip_address, user_agent
    )

    return token_data


@router.post("/logout", response_model=ResponseBase, summary="用户登出")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户登出"""
    # 从 Header 获取 Token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        auth_service = AuthService(db)
        await auth_service.logout(current_user.id, token)

    return {"message": "登出成功"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """使用刷新令牌获取新的访问令牌"""
    auth_service = AuthService(db)
    return await auth_service.refresh_token(data.refresh_token)


@router.post("/register", response_model=dict, summary="用户注册")
async def register(
    register_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    用户注册

    - **username**: 用户名
    - **password**: 密码
    - **email**: 邮箱
    - **phone**: 手机号 (可选)
    - **verify_code**: 验证码
    """
    auth_service = AuthService(db)
    ip_address = request.client.host

    user = await auth_service.register(register_data, ip_address)

    return {
        "message": "注册成功",
        "data": {"user_id": user.id, "username": user.username},
    }


@router.post("/change-password", response_model=ResponseBase, summary="修改密码")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    auth_service = AuthService(db)
    await auth_service.change_password(current_user.id, change_data)
    return {"message": "密码修改成功"}


@router.post("/send-verify-code", response_model=ResponseBase, summary="发送验证码")
async def send_verify_code(
    data: SendVerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """
    发送验证码

    - **email**: 邮箱 (二选一)
    - **phone**: 手机号 (二选一)
    - **type**: verify(验证)/login(登录)/reset(重置密码)
    """
    from ..services.auth_service import AuthService
    from ..core.config import settings

    auth_service = AuthService(db)
    await auth_service.send_verify_code(data.email, data.phone, data.type)

    # 开发环境：返回验证码（方便测试）
    if settings.DEBUG:
        identifier = data.email or data.phone
        from ..services.redis_service import redis_service
        code = redis_service.get_verify_code(data.type, identifier)
        return {"message": f"验证码已发送（测试模式：{code}）"}

    return {"message": "验证码已发送"}


@router.post("/verify-code", response_model=ResponseBase, summary="验证验证码")
async def verify_code(
    data: VerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """验证验证码"""
    from ..services.redis_service import redis_service

    identifier = data.email or data.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="邮箱或手机号必须提供一个")

    stored_code = redis_service.get_verify_code(data.type, identifier)

    if not stored_code or stored_code != data.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证成功后删除验证码
    redis_service.delete_verify_code(data.type, identifier)

    return {"message": "验证成功"}


@router.get("/me", response_model=dict, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "dept_id": current_user.dept_id,
        "status": current_user.status,
        "email_verified": current_user.email_verified,
        "phone_verified": current_user.phone_verified,
        "last_login_time": current_user.last_login_time.isoformat()
        if current_user.last_login_time
        else None,
    }
