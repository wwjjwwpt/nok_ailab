-- ============================================================
-- NOK AI Lab - 企业级权限管理系统数据库初始化脚本
-- PostgreSQL 16+
-- ============================================================
-- 所有表都包含：created_at, updated_at, status 字段

-- 使用方法:
-- psql -h <host> -U postgres -d nok_ailab -f init.sql

-- ============================================================
-- 1. 创建扩展 (需要超级用户权限，如失败请跳过)
-- ============================================================
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 2. 创建表结构
-- ============================================================

-- 部门表
CREATE TABLE IF NOT EXISTS departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_id BIGINT DEFAULT 0,
    leader_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    sort_order SMALLINT DEFAULT 0,
    full_path VARCHAR(500),
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    nickname VARCHAR(50),
    dept_id BIGINT REFERENCES departments(id),
    avatar VARCHAR(500),
    status SMALLINT DEFAULT 1,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    last_login_time TIMESTAMP,
    last_login_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_system BOOLEAN DEFAULT FALSE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 菜单表
CREATE TABLE IF NOT EXISTS menus (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_id BIGINT DEFAULT 0,
    path VARCHAR(200),
    component VARCHAR(200),
    icon VARCHAR(50),
    type SMALLINT,
    sort_order SMALLINT DEFAULT 0,
    visible BOOLEAN DEFAULT TRUE,
    permission VARCHAR(100),
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 功能权限表
CREATE TABLE IF NOT EXISTS permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    menu_id BIGINT REFERENCES menus(id),
    type VARCHAR(20),
    api_method VARCHAR(10),
    api_path VARCHAR(200),
    description VARCHAR(255),
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 数据权限规则表
CREATE TABLE IF NOT EXISTS data_scopes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    scope_type SMALLINT NOT NULL,
    scope_config JSONB,
    description VARCHAR(255),
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 用户 - 角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- 角色 - 菜单关联表
CREATE TABLE IF NOT EXISTS role_menus (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    menu_id BIGINT REFERENCES menus(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, menu_id)
);

-- 角色 - 权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    permission_id BIGINT REFERENCES permissions(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- 角色 - 数据权限关联表
CREATE TABLE IF NOT EXISTS role_data_scopes (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    data_scope_id BIGINT REFERENCES data_scopes(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, data_scope_id)
);

-- 用户直接权限表 (特殊授权)
CREATE TABLE IF NOT EXISTS user_permissions (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    permission_id BIGINT REFERENCES permissions(id) ON DELETE CASCADE,
    grant_type SMALLINT DEFAULT 1,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, permission_id)
);

-- 用户直接数据权限表
CREATE TABLE IF NOT EXISTS user_data_scopes (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    data_scope_id BIGINT REFERENCES data_scopes(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, data_scope_id)
);

-- 登录日志表
CREATE TABLE IF NOT EXISTS login_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    username VARCHAR(50),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    login_status VARCHAR(20),
    fail_reason VARCHAR(255),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    username VARCHAR(50),
    module VARCHAR(50),
    operation VARCHAR(50),
    method VARCHAR(10),
    request_url VARCHAR(500),
    request_params TEXT,
    ip_address VARCHAR(50),
    duration_ms BIGINT,
    status VARCHAR(20),
    error_msg TEXT,
    operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. 创建索引
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_depts_parent_id ON departments(parent_id);
CREATE INDEX IF NOT EXISTS idx_depts_status ON departments(status);

CREATE INDEX IF NOT EXISTS idx_users_dept_id ON users(dept_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

CREATE INDEX IF NOT EXISTS idx_roles_code ON roles(code);
CREATE INDEX IF NOT EXISTS idx_roles_status ON roles(status);

CREATE INDEX IF NOT EXISTS idx_menus_parent_id ON menus(parent_id);
CREATE INDEX IF NOT EXISTS idx_menus_code ON menus(code);
CREATE INDEX IF NOT EXISTS idx_menus_status ON menus(status);

CREATE INDEX IF NOT EXISTS idx_permissions_code ON permissions(code);
CREATE INDEX IF NOT EXISTS idx_permissions_menu_id ON permissions(menu_id);
CREATE INDEX IF NOT EXISTS idx_permissions_status ON permissions(status);

CREATE INDEX IF NOT EXISTS idx_data_scopes_code ON data_scopes(code);
CREATE INDEX IF NOT EXISTS idx_data_scopes_status ON data_scopes(status);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

CREATE INDEX IF NOT EXISTS idx_role_menus_role ON role_menus(role_id);
CREATE INDEX IF NOT EXISTS idx_role_menus_menu ON role_menus(menu_id);

CREATE INDEX IF NOT EXISTS idx_role_perms_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_perms_perm ON role_permissions(permission_id);

CREATE INDEX IF NOT EXISTS idx_login_logs_user ON login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_login_logs_username ON login_logs(username);
CREATE INDEX IF NOT EXISTS idx_login_logs_time ON login_logs(login_time);

CREATE INDEX IF NOT EXISTS idx_operation_logs_user ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_time ON operation_logs(operation_time);

-- ============================================================
-- 4. 初始化基础数据
-- ============================================================

-- 4.1 创建默认部门
INSERT INTO departments (id, name, parent_id, full_path, status)
VALUES (1, '默认部门', 0, '/1/', 1)
ON CONFLICT (id) DO NOTHING;

-- 4.2 创建系统角色
INSERT INTO roles (id, name, code, description, is_system, status) VALUES
(1, '超级管理员', 'admin', '系统超级管理员，拥有所有权限', TRUE, 1),
(2, '普通用户', 'user', '普通用户，基础权限', TRUE, 1)
ON CONFLICT (id) DO NOTHING;

-- 4.3 创建数据权限规则
INSERT INTO data_scopes (id, name, code, scope_type, description, status) VALUES
(1, '全部数据', 'all', 1, '可访问全部数据', 1),
(2, '本部门及子部门', 'dept_and_children', 2, '可访问本部门及下级部门数据', 1),
(3, '本部门', 'dept', 3, '仅访问本部门数据', 1),
(4, '仅本人', 'self', 4, '仅访问本人创建的数据', 1)
ON CONFLICT (id) DO NOTHING;

-- 4.4 创建系统菜单
INSERT INTO menus (id, name, code, parent_id, path, component, icon, type, sort_order, visible, status) VALUES
(1, '系统管理', 'system', 0, '/system', NULL, 'Settings', 1, 100, TRUE, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO menus (id, name, code, parent_id, path, component, icon, type, sort_order, visible, status) VALUES
(10, '用户管理', 'system_user', 1, '/system/user', 'system/user/index', 'User', 2, 1, TRUE, 1),
(11, '角色管理', 'system_role', 1, '/system/role', 'system/role/index', 'Users', 2, 2, TRUE, 1),
(12, '菜单管理', 'system_menu', 1, '/system/menu', 'system/menu/index', 'Menu', 2, 3, TRUE, 1),
(13, '部门管理', 'system_dept', 1, '/system/dept', 'system/dept/index', 'Users', 2, 4, TRUE, 1),
(14, '权限管理', 'system_perm', 1, '/system/permission', 'system/permission/index', 'Lock', 2, 5, TRUE, 1),
(15, '数据权限', 'system_data_scope', 1, '/system/data-scope', 'system/data_scope/index', 'Database', 2, 6, TRUE, 1),
(16, '日志管理', 'system_log', 1, '/system/log', 'system/log/index', 'FileText', 2, 7, TRUE, 1)
ON CONFLICT (id) DO NOTHING;

-- 4.5 创建功能权限
INSERT INTO permissions (id, name, code, menu_id, type, api_method, api_path, description, status) VALUES
-- 用户管理权限
(101, '查看用户', 'user:view', 10, 'button', 'GET', '/api/v1/users', '查看用户列表', 1),
(102, '新增用户', 'user:add', 10, 'button', 'POST', '/api/v1/users', '新增用户', 1),
(103, '编辑用户', 'user:edit', 10, 'button', 'PUT', '/api/v1/users/*', '编辑用户', 1),
(104, '删除用户', 'user:delete', 10, 'button', 'DELETE', '/api/v1/users/*', '删除用户', 1),
(105, '分配角色', 'user:assign_role', 10, 'button', 'POST', '/api/v1/users/*/roles', '分配角色', 1),
-- 角色管理权限
(201, '查看角色', 'role:view', 11, 'button', 'GET', '/api/v1/roles', '查看角色列表', 1),
(202, '新增角色', 'role:add', 11, 'button', 'POST', '/api/v1/roles', '新增角色', 1),
(203, '编辑角色', 'role:edit', 11, 'button', 'PUT', '/api/v1/roles/*', '编辑角色', 1),
(204, '删除角色', 'role:delete', 11, 'button', 'DELETE', '/api/v1/roles/*', '删除角色', 1),
(205, '分配权限', 'role:assign_perm', 11, 'button', 'POST', '/api/v1/roles/*/permissions', '分配权限', 1),
-- 菜单管理权限
(301, '查看菜单', 'menu:view', 12, 'button', 'GET', '/api/v1/menus', '查看菜单', 1),
(302, '新增菜单', 'menu:add', 12, 'button', 'POST', '/api/v1/menus', '新增菜单', 1),
(303, '编辑菜单', 'menu:edit', 12, 'button', 'PUT', '/api/v1/menus/*', '编辑菜单', 1),
(304, '删除菜单', 'menu:delete', 12, 'button', 'DELETE', '/api/v1/menus/*', '删除菜单', 1),
-- 部门管理权限
(401, '查看部门', 'dept:view', 13, 'button', 'GET', '/api/v1/departments', '查看部门', 1),
(402, '新增部门', 'dept:add', 13, 'button', 'POST', '/api/v1/departments', '新增部门', 1),
(403, '编辑部门', 'dept:edit', 13, 'button', 'PUT', '/api/v1/departments/*', '编辑部门', 1),
(404, '删除部门', 'dept:delete', 13, 'button', 'DELETE', '/api/v1/departments/*', '删除部门', 1),
-- 权限管理权限
(501, '查看权限', 'permission:view', 14, 'button', 'GET', '/api/v1/permissions', '查看权限', 1),
(502, '新增权限', 'permission:add', 14, 'button', 'POST', '/api/v1/permissions', '新增权限', 1),
(503, '编辑权限', 'permission:edit', 14, 'button', 'PUT', '/api/v1/permissions/*', '编辑权限', 1),
(504, '删除权限', 'permission:delete', 14, 'button', 'DELETE', '/api/v1/permissions/*', '删除权限', 1),
-- 数据权限权限
(601, '查看数据权限', 'data_scope:view', 15, 'button', 'GET', '/api/v1/data-scopes', '查看数据权限', 1),
(602, '新增数据权限', 'data_scope:add', 15, 'button', 'POST', '/api/v1/data-scopes', '新增数据权限', 1),
(603, '编辑数据权限', 'data_scope:edit', 15, 'button', 'PUT', '/api/v1/data-scopes/*', '编辑数据权限', 1),
(604, '删除数据权限', 'data_scope:delete', 15, 'button', 'DELETE', '/api/v1/data-scopes/*', '删除数据权限', 1),
-- 日志管理权限
(701, '查看日志', 'log:view', 16, 'button', 'GET', '/api/v1/logs/*', '查看日志', 1),
(702, '导出日志', 'log:export', 16, 'button', 'GET', '/api/v1/logs/*/export', '导出日志', 1)
ON CONFLICT (id) DO NOTHING;

-- 4.6 分配管理员角色给默认菜单和权限
INSERT INTO role_menus (role_id, menu_id, status)
SELECT 1, id, 1 FROM menus
WHERE NOT EXISTS (SELECT 1 FROM role_menus WHERE role_id=1 AND menu_id=menus.id);

INSERT INTO role_permissions (role_id, permission_id, status)
SELECT 1, id, 1 FROM permissions
WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=1 AND permission_id=permissions.id);

-- 4.7 创建默认管理员账号 (密码：admin123)
INSERT INTO users (id, username, password, email, nickname, dept_id, status, email_verified)
VALUES (
    1,
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYJWCz0pFZG',
    'admin@example.com',
    '管理员',
    1,
    1,
    TRUE
)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    nickname = EXCLUDED.nickname;

-- 4.8 分配管理员角色
INSERT INTO user_roles (user_id, role_id, status)
VALUES (1, 1, 1)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 4.9 分配角色数据权限
INSERT INTO role_data_scopes (role_id, data_scope_id, status)
VALUES (1, 1, 1)  -- 管理员拥有全部数据权限
ON CONFLICT (role_id, data_scope_id) DO NOTHING;

-- ============================================================
-- 5. 更新序列
-- ============================================================

SELECT setval('departments_id_seq', COALESCE((SELECT MAX(id) FROM departments), 0) + 1, FALSE);
SELECT setval('roles_id_seq', COALESCE((SELECT MAX(id) FROM roles), 0) + 1, FALSE);
SELECT setval('data_scopes_id_seq', COALESCE((SELECT MAX(id) FROM data_scopes), 0) + 1, FALSE);
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 0) + 1, FALSE);
SELECT setval('menus_id_seq', COALESCE((SELECT MAX(id) FROM menus), 0) + 1, FALSE);
SELECT setval('permissions_id_seq', COALESCE((SELECT MAX(id) FROM permissions), 0) + 1, FALSE);

-- ============================================================
-- 6. 完成提示
-- ============================================================

SELECT '数据库初始化完成!' AS status,
       (SELECT COUNT(*) FROM users) AS users_count,
       (SELECT COUNT(*) FROM roles) AS roles_count,
       (SELECT COUNT(*) FROM menus) AS menus_count,
       (SELECT COUNT(*) FROM permissions) AS permissions_count,
       (SELECT COUNT(*) FROM departments) AS departments_count;
