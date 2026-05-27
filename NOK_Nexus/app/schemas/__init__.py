"""
Pydantic Schemas - 数据验证模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==================== 用户相关 Schema ====================


class UserBase(BaseModel):
    """用户基础模型"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    nickname: Optional[str] = Field(None, max_length=50)
    dept_id: Optional[int] = None


class UserCreate(UserBase):
    """创建用户"""

    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(UserBase):
    """更新用户"""

    password: Optional[str] = Field(None, min_length=6, max_length=128)
    avatar: Optional[str] = None
    status: Optional[int] = None


class UserResponse(UserBase):
    """用户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dept_id: Optional[int] = None
    avatar: Optional[str] = None
    status: int
    email_verified: bool
    phone_verified: bool
    last_login_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """用户登录"""

    username: str
    password: str
    verify_code: Optional[str] = None  # 验证码


class UserRegister(BaseModel):
    """用户注册"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    email: EmailStr
    phone: Optional[str] = None
    verify_code: str  # 验证码


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间 (秒)


class RefreshTokenRequest(BaseModel):
    """刷新 Token"""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码"""

    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class SendVerifyCodeRequest(BaseModel):
    """发送验证码"""

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    type: str = Field(..., description="verify: 验证，login: 登录，reset: 重置密码")


class VerifyCodeRequest(BaseModel):
    """验证验证码"""

    email: Optional[str] = None
    phone: Optional[str] = None
    code: str
    type: str


# ==================== 角色相关 Schema ====================


class RoleBase(BaseModel):
    """角色基础模型"""

    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """创建角色"""

    permission_ids: Optional[List[int]] = []
    menu_ids: Optional[List[int]] = []
    data_scope_ids: Optional[List[int]] = []


class RoleUpdate(RoleBase):
    """更新角色"""

    id: int
    permission_ids: Optional[List[int]] = []
    menu_ids: Optional[List[int]] = []
    data_scope_ids: Optional[List[int]] = []


class RoleResponse(RoleBase):
    """角色响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleHierarchyResponse(BaseModel):
    """角色层级响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_role_id: int
    child_role_id: int
    status: int
    created_at: datetime


class RoleWithHierarchyResponse(RoleResponse):
    """带层级信息的角色响应"""

    parent_roles: List[dict] = []
    child_roles: List[dict] = []
    permissions: List[dict] = []


# ==================== 菜单相关 Schema ====================


class MenuBase(BaseModel):
    """菜单基础模型"""

    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    parent_id: int = 0
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    type: int = Field(2, description="1-目录 2-菜单 3-外链")
    sort_order: int = 0
    visible: bool = True
    permission: Optional[str] = None


class MenuCreate(MenuBase):
    """创建菜单"""


class MenuUpdate(MenuBase):
    """更新菜单"""

    id: int


class MenuResponse(MenuBase):
    """菜单响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    children: List["MenuResponse"] = []


# ==================== 权限相关 Schema ====================


class PermissionBase(BaseModel):
    """权限基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限编码")
    menu_ids: Optional[List[int]] = Field(default=[], description="关联的菜单 ID 列表")
    description: Optional[str] = Field(None, description="描述")


class PermissionCreate(PermissionBase):
    """创建权限"""


class PermissionUpdate(PermissionBase):
    """更新权限"""

    id: int


class PermissionResponse(PermissionBase):
    """权限响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: int = 1
    created_at: datetime
    updated_at: datetime


# ==================== 数据权限相关 Schema ====================


class DataScopeBase(BaseModel):
    """数据权限基础模型"""

    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    scope_type: int = Field(
        ..., description="1-全部 2-本部门及子部门 3-本部门 4-本人 5-自定义"
    )
    scope_config: Optional[dict] = None
    description: Optional[str] = None


class DataScopeCreate(DataScopeBase):
    """创建数据权限"""


class DataScopeUpdate(DataScopeBase):
    """更新数据权限"""

    id: int


class DataScopeResponse(DataScopeBase):
    """数据权限响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==================== 部门相关 Schema ====================


class DepartmentBase(BaseModel):
    """部门基础模型"""

    name: str = Field(..., min_length=1, max_length=50)
    parent_id: int = 0
    leader_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    sort_order: int = 0


class DepartmentCreate(DepartmentBase):
    """创建部门"""


class DepartmentUpdate(DepartmentBase):
    """更新部门"""

    id: int


class DepartmentResponse(DepartmentBase):
    """部门响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    children: List["DepartmentResponse"] = []


# ==================== 日志相关 Schema ====================


class LoginLogResponse(BaseModel):
    """登录日志响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: str
    ip_address: Optional[str] = None
    login_status: str
    fail_reason: Optional[str] = None
    login_time: datetime


class OperationLogResponse(BaseModel):
    """操作日志响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: str
    module: str
    operation: str
    method: str
    request_url: str
    ip_address: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str
    error_msg: Optional[str] = None
    operation_time: datetime


# ==================== 通用响应 ====================


class ResponseBase(BaseModel):
    """通用响应基类"""

    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class PageResponse(BaseModel):
    """分页响应"""

    items: List
    total: int
    page: int
    page_size: int
    has_next: bool
