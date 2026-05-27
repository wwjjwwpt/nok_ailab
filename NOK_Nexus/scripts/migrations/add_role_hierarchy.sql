-- 添加角色层级关系表
-- 父角色继承子角色的权限

-- 创建角色层级关系表
CREATE TABLE IF NOT EXISTS role_hierarchy (
    id BIGSERIAL PRIMARY KEY,
    parent_role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    child_role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_parent_child UNIQUE (parent_role_id, child_role_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_role_hierarchy_parent ON role_hierarchy(parent_role_id);
CREATE INDEX IF NOT EXISTS idx_role_hierarchy_child ON role_hierarchy(child_role_id);

-- 添加注释
COMMENT ON TABLE role_hierarchy IS '角色层级关系表 - 父角色继承子角色的权限';
COMMENT ON COLUMN role_hierarchy.parent_role_id IS '父角色 ID';
COMMENT ON COLUMN role_hierarchy.child_role_id IS '子角色 ID';
COMMENT ON COLUMN role_hierarchy.status IS '状态：0-禁用 1-正常';
