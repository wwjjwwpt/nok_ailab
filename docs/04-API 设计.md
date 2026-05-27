# API 设计

## API 规范

### 基础信息
- **基础路径**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

### 响应格式

**成功响应**:
```json
{
  "data": { ... },
  "message": "success"
}
```

**错误响应**:
```json
{
  "detail": "错误信息"
}
```

**列表响应**:
```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

## API 列表

### 认证模块 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login` | 用户登录 |
| POST | `/logout` | 用户登出 |
| POST | `/refresh` | 刷新 Token |
| GET | `/userinfo` | 获取当前用户信息 |

### 用户管理 `/api/v1/users`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users` | 用户列表 |
| GET | `/users/:id` | 用户详情 |
| POST | `/users` | 创建用户 |
| PUT | `/users/:id` | 更新用户 |
| DELETE | `/users/:id` | 删除用户 |
| POST | `/users/:id/roles` | 分配角色 |

### 角色管理 `/api/v1/roles`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/roles` | 角色列表 |
| GET | `/roles/:id` | 角色详情 |
| POST | `/roles` | 创建角色 |
| PUT | `/roles/:id` | 更新角色 |
| DELETE | `/roles/:id` | 删除角色 |
| POST | `/roles/:id/permissions` | 分配功能权限 |
| POST | `/roles/:id/data-scopes` | 分配数据权限 |

### 菜单管理 `/api/v1/menus`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/menus` | 菜单列表 |
| GET | `/menus/tree` | 菜单树 |
| GET | `/menus/user` | 当前用户菜单 |
| POST | `/menus` | 创建菜单 |
| PUT | `/menus/:id` | 更新菜单 |
| DELETE | `/menus/:id` | 删除菜单 |

### 权限管理 `/api/v1/permissions`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/permissions` | 权限列表 |
| POST | `/permissions` | 创建权限 |
| PUT | `/permissions/:id` | 更新权限 |
| DELETE | `/permissions/:id` | 删除权限 |

### 数据权限 `/api/v1/data-scopes`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/data-scopes` | 数据权限列表 |
| POST | `/data-scopes` | 创建数据权限 |
| PUT | `/data-scopes/:id` | 更新数据权限 |
| DELETE | `/data-scopes/:id` | 删除数据权限 |

### 部门管理 `/api/v1/departments`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/departments` | 部门列表 |
| GET | `/departments/tree` | 部门树 |
| POST | `/departments` | 创建部门 |
| PUT | `/departments/:id` | 更新部门 |
| DELETE | `/departments/:id` | 删除部门 |

### 日志管理 `/api/v1/logs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/logs/login` | 登录日志列表 |
| GET | `/logs/operation` | 操作日志列表 |
| GET | `/logs/:id/export` | 导出日志 |

## 权限计算逻辑

### 菜单权限计算
```
用户可见菜单 = 角色菜单 ∪ 直接授权菜单
```

### 功能权限计算
```
用户功能权限 = (所有角色的权限) ∪ 直接授权权限
```

### 数据权限计算
```
用户数据权限 = 优先级最高的角色数据权限
优先级：全部 > 本部门及子部门 > 本部门 > 仅本人
```
