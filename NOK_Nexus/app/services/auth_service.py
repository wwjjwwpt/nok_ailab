"""
认证服务
处理用户登录、注册、Token 刷新等
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models import User, LoginLog
from ..schemas import UserLogin, UserRegister, ChangePasswordRequest
from .redis_service import redis_service
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ..core.config import settings


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def login(
        self, login_data: UserLogin, ip_address: str, user_agent: str
    ) -> Tuple[User, dict]:
        """
        用户登录
        :return: (用户对象，Token 信息)
        """
        # 1. 查找用户
        user = (
            self.db.query(User)
            .filter(
                (User.username == login_data.username)
                | (User.email == login_data.username)
                | (User.phone == login_data.username)
            )
            .first()
        )

        if not user:
            # 记录登录失败日志
            self._log_login(
                username=login_data.username,
                ip_address=ip_address,
                status="fail",
                fail_reason="用户不存在",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        # 2. 检查用户状态
        if user.status != 1:
            self._log_login(
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
                status="fail",
                fail_reason="用户已禁用",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用",
            )

        # 3. 验证密码
        if not verify_password(login_data.password, user.password):
            self._log_login(
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
                status="fail",
                fail_reason="密码错误",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        # 4. 生成 Token
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # 5. 更新用户登录信息
        user.last_login_time = datetime.utcnow()
        user.last_login_ip = ip_address
        self.db.commit()

        # 6. 记录登录日志
        self._log_login(
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
        )

        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

        return user, token_data

    async def register(
        self, register_data: UserRegister, ip_address: str
    ) -> User:
        """
        用户注册
        """
        # 1. 检查用户名是否已存在
        existing_user = (
            self.db.query(User)
            .filter(
                (User.username == register_data.username)
                | (User.email == register_data.email)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在",
            )

        # 2. 验证验证码（邮箱或手机号）
        identifier = register_data.email or register_data.phone
        if identifier:
            verify_code = redis_service.get_verify_code("verify", identifier)
            if not verify_code or verify_code != register_data.verify_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码错误",
                )

        # 3. 创建用户
        user = User(
            username=register_data.username,
            password=get_password_hash(register_data.password),
            email=register_data.email,
            phone=register_data.phone,
            nickname=register_data.username,
            status=1,
            email_verified=True if register_data.email else False,
            phone_verified=True if register_data.phone else False,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 4. 删除验证码
        if identifier:
            redis_service.delete_verify_code("verify", identifier)

        return user

    async def logout(self, user_id: int, token: str) -> None:
        """
        用户登出
        将 Token 加入黑名单
        """
        # 解码 token 获取过期时间
        payload = decode_token(token)
        if payload:
            exp = payload.get("exp")
            if exp:
                # 计算剩余有效时间
                now = datetime.utcnow().timestamp()
                expire_seconds = max(0, int(exp - now))
                if expire_seconds > 0:
                    await redis_service.blacklist_token(
                        token, expire_seconds // 3600 + 1
                    )

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        刷新 Token
        """
        # 1. 验证刷新令牌
        payload = decode_token(refresh_token)

        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期",
            )

        # 2. 获取用户
        user_id = payload.get("sub")
        user = self.db.query(User).filter(User.id == int(user_id)).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
            )

        if user.status != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用",
            )

        # 3. 生成新的 Token
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def change_password(
        self, user_id: int, change_data: ChangePasswordRequest
    ) -> None:
        """
        修改密码
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        # 验证旧密码
        if not verify_password(change_data.old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误",
            )

        # 更新密码
        user.password = get_password_hash(change_data.new_password)
        self.db.commit()

    async def send_verify_code(
        self, email: Optional[str], phone: Optional[str], type: str
    ) -> None:
        """
        发送验证码
        """
        import random

        # 生成 6 位验证码
        code = str(random.randint(100000, 999999))

        identifier = email or phone
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱或手机号必须提供一个",
            )

        # 设置验证码 (实际项目中这里应该调用短信/邮件服务)
        redis_service.set_verify_code(type, identifier, code, expire_minutes=10)

        # TODO: 调用短信/邮件服务发送验证码
        # 开发环境可以直接打印
        print(f"验证码 [{type}]: {identifier} -> {code}")

    def _log_login(
        self,
        username: str,
        ip_address: str,
        status: str,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        fail_reason: Optional[str] = None,
    ) -> None:
        """记录登录日志"""
        log = LoginLog(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            login_status=status,
            fail_reason=fail_reason,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
