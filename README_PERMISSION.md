# NOK AI Lab 权限管理系统

## 系统架构

### 技术栈
- **前端**: Next.js 15 + React + TypeScript + Ant Design
- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **认证**: JWT (Access Token + Refresh Token)
- **权限模型**: RBAC + 数据权限混合模型

## 权限系统设计

### 1. 菜单结构

```
仪表板 (dashboard)
系统管理 (system)
├── 用户管理 (system_user)
├── 角色管理 (system_role)
├── 菜单管理 (system_menu)
├── 权限管理 (system_permission)
├── 部门管理 (system_dept)
├── 数据权限 (system_data_scope)
└── 日志管理 (system_log)
```

### 2. 功能权限编码

| 模块 | 权限编码 | 说明 |
|------|----------|------|
| 用户管理 | user:view | 查看用户 |
|  | user:add | 新增用户 |
|  | user:edit | 编辑用户 |
|  | user:delete | 删除用户 |
|  | user:assign_role | 分配角色 |
| 角色管理 | role:view | 查看角色 |
|  | role:add | 新增角色 |
|  | role:edit | 编辑角色 |
|  | role:delete | 删除角色 |
|  | role:assign_permission | 分配权限 |
| 菜单管理 | menu:view | 查看菜单 |
|  | menu:add | 新增菜单 |
|  | menu:edit | 编辑菜单 |
|  | menu:delete | 删除菜单 |
| 权限管理 | permission:view | 查看权限 |
|  | permission:add | 新增权限 |
|  | permission:edit | 编辑权限 |
|  | permission:delete | 删除权限 |
| 部门管理 | dept:view | 查看部门 |
|  | dept:add | 新增部门 |
|  | dept:edit | 编辑部门 |
|  | dept:delete | 删除部门 |
| 数据权限 | data_scope:view | 查看数据权限 |
|  | data_scope:add | 新增数据权限 |
|  | data_scope:edit | 编辑数据权限 |
|  | data_scope:delete | 删除数据权限 |
| 日志管理 | log:view_login | 查看登录日志 |
|  | log:view_operation | 查看操作日志 |

### 3. 数据权限范围

| 类型 | 编码 | 说明 |
|------|------|------|
| 全部数据 | all | 可访问系统中的全部数据 |
| 本部门及子部门 | dept_and_children | 可访问本部门及所有下级部门的数据 |
| 本部门 | dept | 仅可访问本部门的数据 |
| 仅本人 | self | 仅可访问自己创建的数据 |
| 自定义范围 | custom | 可指定特定的部门范围 |

## 数据库模型

### 核心表
- `users` - 用户表
- `roles` - 角色表
- `menus` - 菜单表
- `permissions` - 功能权限表
- `data_scopes` - 数据权限表
- `departments` - 部门表

### 关联表
- `user_roles` - 用户 - 角色关联
- `role_menus` - 角色 - 菜单关联
- `role_permissions` - 角色 - 权限关联
- `role_data_scopes` - 角色 - 数据权限关联
- `user_permissions` - 用户直接权限 (特殊授权)
- `user_data_scopes` - 用户直接数据权限

### 日志表
- `login_logs` - 登录日志
- `operation_logs` - 操作日志

## 管理页面

### 用户管理 `/system/user`
- 用户列表展示 (分页、搜索)
- 创建/编辑用户
- 分配角色
- 用户状态管理

### 角色管理 `/system/role`
- 角色列表展示
- 创建/编辑角色
- 分配菜单权限 (树形选择)
- 分配功能权限 (复选框)
- 分配数据权限

### 菜单管理 `/system/menu`
- 菜单树形展示
- 创建/编辑菜单
- 配置菜单类型 (目录/菜单/外链)
- 配置路由路径和组件
- 配置图标和权限标识

### 权限管理 `/system/permission`
- 权限列表展示
- 按菜单筛选权限
- 创建/编辑权限
- 配置权限类型 (按钮/接口)
- 配置 API 方法和路径

### 部门管理 `/system/dept`
- 部门树形结构展示
- 创建/编辑部门
- 设置负责人和联系方式
- 部门排序

### 数据权限管理 `/system/data-scope`
- 数据权限规则展示
- 配置数据权限范围类型
- 自定义部门范围选择

### 日志管理 `/system/log`
- 登录日志查询
- 操作日志查询
- 支持按用户名、状态、模块筛选

## 前端权限控制

### 菜单权限
- 登录时获取用户可访问的菜单树
- 根据菜单树动态生成侧边导航
- 无权限菜单不显示

### 功能权限
- 通过 `useMenuStore.hasPermission()` 检查权限
- 控制按钮级别的显示/隐藏
- 配合后端 API 权限验证

### API 接口权限
- 使用 `PermissionDependency` 装饰器
- 后端校验用户权限码
- 无权限返回 403

## 默认账号

**管理员账号**: `admin` / `admin123`
- 拥有所有菜单和功能权限
- 拥有全部数据权限

**普通用户角色**: `user`
- 仅拥有仪表板菜单权限

## API 端点

### 认证
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/refresh` - 刷新 Token
- `POST /api/v1/auth/register` - 用户注册
- `GET /api/v1/auth/me` - 获取当前用户

### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `GET /api/v1/users/{id}` - 获取用户详情
- `POST /api/v1/users` - 创建用户
- `PUT /api/v1/users/{id}` - 更新用户
- `DELETE /api/v1/users/{id}` - 删除用户
- `POST /api/v1/users/{id}/roles` - 分配角色
- `GET /api/v1/users/{id}/roles` - 获取用户角色

### 角色管理
- `GET /api/v1/roles` - 获取角色列表
- `GET /api/v1/roles/{id}` - 获取角色详情
- `POST /api/v1/roles` - 创建角色
- `PUT /api/v1/roles/{id}` - 更新角色
- `DELETE /api/v1/roles/{id}` - 删除角色
- `GET /api/v1/roles/{id}/permissions` - 获取角色权限
- `POST /api/v1/roles/{id}/permissions` - 分配权限

### 菜单管理
- `GET /api/v1/menus/tree` - 获取用户菜单树
- `GET /api/v1/menus` - 获取所有菜单
- `POST /api/v1/menus` - 创建菜单
- `PUT /api/v1/menus/{id}` - 更新菜单
- `DELETE /api/v1/menus/{id}` - 删除菜单

### 权限管理
- `GET /api/v1/permissions` - 获取权限列表
- `POST /api/v1/permissions` - 创建权限
- `PUT /api/v1/permissions/{id}` - 更新权限
- `DELETE /api/v1/permissions/{id}` - 删除权限

### 部门管理
- `GET /api/v1/departments/tree` - 获取部门树
- `GET /api/v1/departments` - 获取部门列表
- `POST /api/v1/departments` - 创建部门
- `PUT /api/v1/departments/{id}` - 更新部门
- `DELETE /api/v1/departments/{id}` - 删除部门

### 日志管理
- `GET /api/v1/logs/login` - 获取登录日志
- `GET /api/v1/logs/operation` - 获取操作日志

## 服务状态

- **后端 API**: http://localhost:8888
- **前端页面**: http://localhost:3001
- **API 文档**: http://localhost:8888/docs

## 环境配置

### 后端 `.env`
```
DATABASE_URL=postgresql://user:password@host:5432/nok_ailab
SECRET_KEY=your-secret-key
DEBUG=True
```

### 前端 `.env.local`
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8888
```
