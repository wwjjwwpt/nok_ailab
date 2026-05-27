-- NOK AI Lab 数据库初始化脚本
-- PostgreSQL 16+

-- 创建数据库 (如未创建)
-- CREATE DATABASE nok_ailab;

-- 连接数据库
-- \c nok_ailab

-- ==================== 扩展 ====================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== 部门表 ====================
CREATE TABLE departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_id BIGINT DEFAULT 0,
    leader_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    sort_order SMALLINT DEFAULT 0,
    full_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_depts_parent_id ON departments(parent_id);
CREATE INDEX idx_depts_full_path ON departments(full_path);

-- ==================== 用户表 ====================
CREATE TABLE users (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_dept_id ON users(dept_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);

-- ==================== 角色表 ====================
CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_roles_code ON roles(code);

-- ==================== 菜单表 ====================
CREATE TABLE menus (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_menus_parent_id ON menus(parent_id);
CREATE INDEX idx_menus_code ON menus(code);

-- ==================== 权限表 ====================
CREATE TABLE permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    menu_id BIGINT REFERENCES menus(id),
    type VARCHAR(20),
    api_method VARCHAR(10),
    api_path VARCHAR(200),
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_permissions_code ON permissions(code);
CREATE INDEX idx_permissions_menu_id ON permissions(menu_id);

-- ==================== 数据权限表 ====================
CREATE TABLE data_scopes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    scope_type SMALLINT NOT NULL,
    scope_config JSONB,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_scopes_code ON data_scopes(code);

-- ==================== 关联表 ====================

-- 用户 - 角色关联
CREATE TABLE user_roles (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- 角色 - 菜单关联
CREATE TABLE role_menus (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    menu_id BIGINT REFERENCES menus(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, menu_id)
);

-- 角色 - 权限关联
CREATE TABLE role_permissions (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    permission_id BIGINT REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 角色 - 数据权限关联
CREATE TABLE role_data_scopes (
    role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
    data_scope_id BIGINT REFERENCES data_scopes(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, data_scope_id)
);

-- 用户直接权限
CREATE TABLE user_permissions (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    permission_id BIGINT REFERENCES permissions(id) ON DELETE CASCADE,
    grant_type SMALLINT DEFAULT 1,
    PRIMARY KEY (user_id, permission_id)
);

-- 用户直接数据权限
CREATE TABLE user_data_scopes (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    data_scope_id BIGINT REFERENCES data_scopes(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, data_scope_id)
);

-- ==================== 日志表 ====================

-- 登录日志
CREATE TABLE login_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    username VARCHAR(50),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    login_status VARCHAR(20),
    fail_reason VARCHAR(255),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_login_logs_user ON login_logs(user_id);
CREATE INDEX idx_login_logs_username ON login_logs(username);
CREATE INDEX idx_login_logs_time ON login_logs(login_time);

-- 操作日志
CREATE TABLE operation_logs (
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

CREATE INDEX idx_operation_logs_user ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_time ON operation_logs(operation_time);

-- ==================== 初始化数据 ====================

-- 默认部门
INSERT INTO departments (id, name, parent_id, full_path) VALUES (1, '默认部门', 0, '/1/');

-- 系统角色
INSERT INTO roles (id, name, code, description, is_system) VALUES
(1, '超级管理员', 'admin', '系统超级管理员，拥有所有权限', TRUE),
(2, '普通用户', 'user', '普通用户，基础权限', TRUE);

-- 数据权限规则
INSERT INTO data_scopes (id, name, code, scope_type, description) VALUES
(1, '全部数据', 'all', 1, '可访问全部数据'),
(2, '本部门及子部门', 'dept_and_children', 2, '可访问本部门及下级部门数据'),
(3, '本部门', 'dept', 3, '仅访问本部门数据'),
(4, '仅本人', 'self', 4, '仅访问本人创建的数据');

-- 默认管理员 (密码：admin123 - bcrypt 哈希)
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
);

-- 分配管理员角色
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1);

-- 更新序列
SELECT setval('departments_id_seq', 1);
SELECT setval('roles_id_seq', 2);
SELECT setval('data_scopes_id_seq', 4);
SELECT setval('users_id_seq', 1);
