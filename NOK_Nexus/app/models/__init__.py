"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    SmallInteger,
    JSON,
    UniqueConstraint,
    Index,
    Numeric,
    Date,
    func,
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    nickname = Column(String(50))
    dept_id = Column(BigInteger, ForeignKey("departments.id"))
    avatar = Column(String(500))
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")
    last_login_time = Column(DateTime)
    last_login_ip = Column(String(50))

    # 邮箱/手机验证码字段
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系
    dept = relationship("Department", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "nickname": self.nickname,
            "dept_id": self.dept_id,
            "avatar": self.avatar,
            "status": self.status,
            "last_login_time": self.last_login_time.isoformat() if self.last_login_time else None,
            "last_login_ip": self.last_login_ip,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))
    is_system = Column(Boolean, default=False, comment="系统内置角色不可删除")
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系
    users = relationship("User", secondary="user_roles", back_populates="roles")
    menus = relationship("Menu", secondary="role_menus", back_populates="roles")
    data_scopes = relationship(
        "DataScope", secondary="role_data_scopes", back_populates="roles"
    )
    # 角色层级关系 - 作为父角色
    parent_of = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.parent_role_id",
        back_populates="parent_role",
        cascade="all, delete-orphan"
    )
    # 角色层级关系 - 作为子角色
    child_of = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.child_role_id",
        back_populates="child_role",
        cascade="all, delete-orphan"
    )


class RoleHierarchy(Base):
    """角色层级关系表 - 父角色继承子角色的权限"""

    __tablename__ = "role_hierarchy"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    parent_role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False, index=True)
    child_role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False, index=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    parent_role = relationship("Role", foreign_keys=[parent_role_id], back_populates="parent_of")
    child_role = relationship("Role", foreign_keys=[child_role_id], back_populates="child_of")

    __table_args__ = (UniqueConstraint("parent_role_id", "child_role_id", name="uk_parent_child"),)


class Menu(Base):
    """菜单表"""

    __tablename__ = "menus"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    parent_id = Column(BigInteger, default=0, index=True)
    path = Column(String(200))
    component = Column(String(200))
    icon = Column(String(50))
    type = Column(SmallInteger, comment="1-目录 2-菜单 3-外链")
    sort_order = Column(SmallInteger, default=0)
    visible = Column(Boolean, default=True)
    permission = Column(String(100), comment="关联权限标识")
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系
    roles = relationship("Role", secondary="role_menus", back_populates="menus")
    permissions = relationship("Permission", secondary="permission_menus", back_populates="menus")


class Permission(Base):
    """功能权限表 - 权限可绑定多个菜单"""

    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="权限名称")
    code = Column(String(100), unique=True, index=True, nullable=False, comment="权限编码如 user:manage")
    description = Column(String(255), comment="描述")
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系 - 通过中间表关联多个菜单
    menus = relationship("Menu", secondary="permission_menus", back_populates="permissions")


class PermissionMenu(Base):
    """权限 - 菜单关联表"""

    __tablename__ = "permission_menus"

    permission_id = Column(BigInteger, ForeignKey("permissions.id"), primary_key=True)
    menu_id = Column(BigInteger, ForeignKey("menus.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")


class DataScope(Base):
    """数据权限规则表"""

    __tablename__ = "data_scopes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    scope_type = Column(SmallInteger, comment="1-全部 2-本部门及子部门 3-本部门 4-本人 5-自定义")
    scope_config = Column(JSON, comment="范围配置 JSON")
    description = Column(String(255))
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系
    roles = relationship(
        "Role", secondary="role_data_scopes", back_populates="data_scopes"
    )


class Department(Base):
    """部门表"""

    __tablename__ = "departments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(BigInteger, default=0, index=True)
    leader_name = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    sort_order = Column(SmallInteger, default=0)
    full_path = Column(String(500), comment="完整路径如/1/5/12/")
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, comment="软删除时间")

    # 关联关系
    users = relationship("User", back_populates="dept")


class UserRole(Base):
    """用户 - 角色关联表"""

    __tablename__ = "user_roles"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("roles.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uk_user_role"),)


class RoleMenu(Base):
    """角色 - 菜单关联表"""

    __tablename__ = "role_menus"

    role_id = Column(BigInteger, ForeignKey("roles.id"), primary_key=True)
    menu_id = Column(BigInteger, ForeignKey("menus.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")


class RolePermission(Base):
    """角色 - 权限关联表"""

    __tablename__ = "role_permissions"

    role_id = Column(BigInteger, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("permissions.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    # 关联关系（不使用 back_populates 避免冲突）
    permission = relationship("Permission")
    role = relationship("Role")


class RoleDataScope(Base):
    """角色 - 数据权限关联表"""

    __tablename__ = "role_data_scopes"

    role_id = Column(BigInteger, ForeignKey("roles.id"), primary_key=True)
    data_scope_id = Column(BigInteger, ForeignKey("data_scopes.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPermission(Base):
    """用户直接权限表 (特殊授权)"""

    __tablename__ = "user_permissions"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("permissions.id"), primary_key=True)
    grant_type = Column(SmallInteger, default=1, comment="1-允许 2-拒绝")
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")


class UserDataSource(Base):
    """用户直接数据权限表"""

    __tablename__ = "user_data_scopes"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    data_scope_id = Column(BigInteger, ForeignKey("data_scopes.id"), primary_key=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")


class LoginLog(Base):
    """登录日志表"""

    __tablename__ = "login_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    username = Column(String(50), index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    login_status = Column(String(20), comment="success/fail")
    fail_reason = Column(String(255))
    login_time = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")

    __table_args__ = (Index("idx_login_logs_user_time", "user_id", "login_time"),)


class OperationLog(Base):
    """操作日志表"""

    __tablename__ = "operation_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    username = Column(String(50))
    module = Column(String(50))
    operation = Column(String(50))
    method = Column(String(10))
    request_url = Column(String(500))
    request_params = Column(Text)
    ip_address = Column(String(50))
    duration_ms = Column(BigInteger)
    status = Column(String(20), comment="success/fail")
    error_msg = Column(Text)
    operation_time = Column(DateTime, default=datetime.utcnow, index=True)
    deleted_at = Column(DateTime, comment="软删除时间")
