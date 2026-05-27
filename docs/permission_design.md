# NOK AI Lab 权限架构设计文档

## 📋 目录

1. [架构概览](#架构概览)
2. [角色层级结构](#角色层级结构)
3. [权限编码规范](#权限编码规范)
4. [菜单 - 权限绑定](#菜单 - 权限绑定)
5. [权限继承机制](#权限继承机制)
6. [数据库表结构](#数据库表结构)

---

## 架构概览

本系统采用 **RBAC (Role-Based Access Control) + 角色层级** 的权限模型：

```
用户 (User)
  ↓
角色 (Role) ←── 父角色继承子角色权限
  ↓
权限 (Permission) ←── 绑定 ──→ 菜单 (Menu)
```

### 核心特性

- ✅ **父角色继承子角色权限**：父角色自动拥有所有子角色的权限
- ✅ **权限 - 菜单绑定**：每个权限关联到具体菜单
- ✅ **角色层级管理**：支持多层级角色继承
- ✅ **数据权限隔离**：基于部门的数据访问控制

---

## 角色层级结构

```
┌─────────────────────────────────────────────────────────┐
│                   nok_admin (父角色)                      │
│              ID=3, 超级管理员，继承所有子角色权限              │
└─────────────────────────────────────────────────────────┘
              │
              ├── 继承 ──────────────────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  user_admin     │  │  role_admin     │  │  dept_admin     │
    │  (子角色)        │  │  (子角色)        │  │  (子角色)        │
    │  ID=4           │  │  ID=5           │  │  ID=6           │
    │                 │  │                 │  │                 │
    │ 用户管理权限：   │  │ 角色/菜单管理权限：│  │ 部门/数据权限：  │
    │ - user:view     │  │ - role:view     │  │ - dept:view     │
    │ - user:add      │  │ - role:add      │  │ - dept:add      │
    │ - user:edit     │  │ - role:edit     │  │ - dept:edit     │
    │ - user:delete   │  │ - role:delete   │  │ - dept:delete   │
    │ - user:assign   │  │ - role:assign   │  │ - data_scope:*  │
    │                 │  │ - menu:*        │  │                 │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 角色说明

| 角色编码 | 角色名称 | 类型 | 描述 |
|---------|---------|------|------|
| `nok_admin` | 超级管理员 | 父角色 | NOK AI Lab 最高权限，自动继承所有子角色权限 |
| `user_admin` | 用户管理员 | 子角色 | 负责用户管理、用户角色分配 |
| `role_admin` | 角色管理员 | 子角色 | 负责角色管理、菜单管理、权限分配 |
| `dept_admin` | 部门管理员 | 子角色 | 负责部门管理、数据权限配置 |

---

## 权限编码规范

### 编码格式

```
{module}:{action}
```

- `module`: 模块标识 (user, role, menu, dept, data_scope, log)
- `action`: 操作类型 (view, add, edit, delete, assign, export, import)

### 权限列表

#### 用户管理权限 (user:*)

| 权限编码 | 权限名称 | 绑定 API | 所属角色 |
|---------|---------|---------|---------|
| `user:view` | 查看用户 | GET /api/v1/users | user_admin |
| `user:add` | 创建用户 | POST /api/v1/users | user_admin |
| `user:edit` | 编辑用户 | PUT /api/v1/users/{id} | user_admin |
| `user:delete` | 删除用户 | DELETE /api/v1/users/{id} | user_admin |
| `user:assign_roles` | 分配角色 | POST /api/v1/users/{id}/roles | user_admin |

#### 角色管理权限 (role:*)

| 权限编码 | 权限名称 | 绑定 API | 所属角色 |
|---------|---------|---------|---------|
| `role:view` | 查看角色 | GET /api/v1/roles | role_admin |
| `role:add` | 创建角色 | POST /api/v1/roles | role_admin |
| `role:edit` | 编辑角色 | PUT /api/v1/roles/{id} | role_admin |
| `role:delete` | 删除角色 | DELETE /api/v1/roles/{id} | role_admin |
| `role:assign_perms` | 分配权限 | POST /api/v1/roles/{id}/permissions | role_admin |

#### 菜单管理权限 (menu:*)

| 权限编码 | 权限名称 | 绑定 API | 所属角色 |
|---------|---------|---------|---------|
| `menu:view` | 查看菜单 | GET /api/v1/menus | role_admin |
| `menu:add` | 创建菜单 | POST /api/v1/menus | role_admin |
| `menu:edit` | 编辑菜单 | PUT /api/v1/menus/{id} | role_admin |
| `menu:delete` | 删除菜单 | DELETE /api/v1/menus/{id} | role_admin |

#### 部门管理权限 (dept:*)

| 权限编码 | 权限名称 | 绑定 API | 所属角色 |
|---------|---------|---------|---------|
| `dept:view` | 查看部门 | GET /api/v1/departments | dept_admin |
| `dept:add` | 创建部门 | POST /api/v1/departments | dept_admin |
| `dept:edit` | 编辑部门 | PUT /api/v1/departments/{id} | dept_admin |
| `dept:delete` | 删除部门 | DELETE /api/v1/departments/{id} | dept_admin |

#### 数据权限管理 (data_scope:*)

| 权限编码 | 权限名称 | 绑定 API | 所属角色 |
|---------|---------|---------|---------|
| `data_scope:view` | 查看数据权限 | GET /api/v1/data-scopes | dept_admin |
| `data_scope:add` | 创建数据权限 | POST /api/v1/data-scopes | dept_admin |
| `data_scope:edit` | 编辑数据权限 | PUT /api/v1/data-scopes/{id} | dept_admin |
| `data_scope:delete` | 删除数据权限 | DELETE /api/v1/data-scopes/{id} | dept_admin |

---

## 菜单 - 权限绑定

每个权限通过 `menu_id` 字段关联到具体菜单：

```sql
-- 权限表结构
CREATE TABLE permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,  -- 如：user:add
    menu_id BIGINT REFERENCES menus(id), -- 关联菜单
    type VARCHAR(20),                     -- button/api
    api_method VARCHAR(10),               -- GET/POST/PUT/DELETE
    api_path VARCHAR(200),                -- API 路径
    ...
);
```

### 菜单树结构

```
系统管理 (system)
├── 用户管理 (user)
│   └── 权限：user:view, user:add, user:edit, user:delete, user:assign_roles
├── 角色管理 (role)
│   └── 权限：role:view, role:add, role:edit, role:delete, role:assign_perms
├── 菜单管理 (menu)
│   └── 权限：menu:view, menu:add, menu:edit, menu:delete
├── 权限管理 (permission)
├── 部门管理 (dept)
│   └── 权限：dept:view, dept:add, dept:edit, dept:delete
├── 数据权限 (data-scope)
│   └── 权限：data_scope:view, data_scope:add, data_scope:edit, data_scope:delete
└── 日志管理 (log)
```

---

## 权限继承机制

### 核心逻辑

```python
def _get_all_role_ids(self, role_ids: List[int]) -> Set[int]:
    """递归获取所有角色 ID（包括父角色）- 父角色继承子角色的权限"""
    all_role_ids = set(role_ids)
    changed = True

    while changed:
        changed = False
        # 查询这些角色作为子角色的父角色
        parent_roles = (
            self.db.query(RoleHierarchy.parent_role_id)
            .filter(
                RoleHierarchy.child_role_id.in_(all_role_ids),
                RoleHierarchy.status == 1
            )
            .all()
        )
        parent_ids = set(pr[0] for pr in parent_roles)
        for pid in parent_ids:
            if pid not in all_role_ids:
                all_role_ids.add(pid)
                changed = True

    return all_role_ids
```

### 继承流程

1. 用户登录，获取用户关联的角色 IDs（如 `[4]` = user_admin）
2. 递归查询父角色：通过 `role_hierarchy` 表找到父角色（如 `[3]` = nok_admin）
3. 合并所有角色 IDs：`[3, 4]`
4. 查询所有角色的权限并集
5. 返回最终权限列表

### 示例

```
用户：admin
  └─ 直接角色：nok_admin (ID=3)
       └─ 子角色：user_admin (ID=4), role_admin (ID=5), dept_admin (ID=6)

最终权限 = nok_admin 的权限 ∪ user_admin 的权限 ∪ role_admin 的权限 ∪ dept_admin 的权限
        = 所有系统管理权限
```

---

## 数据库表结构

### 核心表

| 表名 | 描述 | 关键字段 |
|------|------|---------|
| `users` | 用户表 | id, username, password, email, phone, dept_id, status |
| `roles` | 角色表 | id, name, code, is_system, status |
| `menus` | 菜单表 | id, name, code, parent_id, path, component, type |
| `permissions` | 权限表 | id, name, code, menu_id, type, api_method, api_path |
| `role_hierarchy` | 角色层级表 | parent_role_id, child_role_id |
| `user_roles` | 用户 - 角色关联 | user_id, role_id |
| `role_permissions` | 角色 - 权限关联 | role_id, permission_id |
| `role_menus` | 角色 - 菜单关联 | role_id, menu_id |

### role_hierarchy 表结构

```sql
CREATE TABLE role_hierarchy (
    id BIGSERIAL PRIMARY KEY,
    parent_role_id BIGINT NOT NULL REFERENCES roles(id),
    child_role_id BIGINT NOT NULL REFERENCES roles(id),
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_parent_child UNIQUE (parent_role_id, child_role_id)
);

-- 索引
CREATE INDEX idx_role_hierarchy_parent ON role_hierarchy(parent_role_id);
CREATE INDEX idx_role_hierarchy_child ON role_hierarchy(child_role_id);
```

---

## 默认账号

```
用户名：admin
密码：admin123
角色：nok_admin (超级管理员)
权限：继承所有子角色权限 (user_admin + role_admin + dept_admin)
```

---

## 下一步开发建议

1. **前端权限控制**
   - 按钮级权限控制（基于 `v-if` 或权限指令）
   - 菜单动态加载（基于用户可访问菜单树）
   - 路由守卫（基于权限码）

2. **后端权限验证**
   - 完善 `PermissionDependency` 依赖注入
   - 统一权限异常处理
   - 添加权限缓存（Redis）

3. **扩展功能**
   - 支持一个角色有多个子角色
   - 支持多层级继承（祖父 → 父 → 子）
   - 添加权限审计日志

---

*文档生成时间：2026-03-22*
