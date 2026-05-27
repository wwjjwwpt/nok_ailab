-- 权限模型迁移 - 添加 permission_menus 表
-- 一个权限可以绑定多个菜单

-- 1. 创建 permission_menus 关联表
CREATE TABLE IF NOT EXISTS permission_menus (
    permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    menu_id BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    status SMALLINT DEFAULT 1,
    PRIMARY KEY (permission_id, menu_id)
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_permission_menus_permission ON permission_menus(permission_id);
CREATE INDEX IF NOT EXISTS idx_permission_menus_menu ON permission_menus(menu_id);

-- 3. 删除 permissions 表中不再需要的列
-- 注意：PostgreSQL 不支持 IF EXISTS 语法用于 DROP COLUMN
ALTER TABLE permissions DROP COLUMN IF EXISTS type;
ALTER TABLE permissions DROP COLUMN IF EXISTS api_method;
ALTER TABLE permissions DROP COLUMN IF EXISTS api_path;
ALTER TABLE permissions DROP COLUMN IF EXISTS menu_id;

-- 4. 添加注释
COMMENT ON TABLE permission_menus IS '权限 - 菜单关联表（一个权限可绑定多个菜单）';
COMMENT ON COLUMN permission_menus.permission_id IS '权限 ID';
COMMENT ON COLUMN permission_menus.menu_id IS '菜单 ID';
COMMENT ON COLUMN permission_menus.status IS '状态 0-禁用 1-正常';

-- 迁移完成
SELECT '权限模型迁移完成!' AS status;
