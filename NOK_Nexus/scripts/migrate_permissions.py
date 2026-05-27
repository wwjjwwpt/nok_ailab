"""
权限模型迁移脚本 - 添加 permission_menus 表
"""
import sys
sys.path.insert(0, "..")

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

def migrate():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)

    # 检查 permission_menus 表是否已存在
    tables = inspector.get_table_names()

    if "permission_menus" in tables:
        print("permission_menus 表已存在，跳过创建")
    else:
        print("创建 permission_menus 表...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE permission_menus (
                    permission_id BIGINT NOT NULL,
                    menu_id BIGINT NOT NULL,
                    status SMALLINT DEFAULT 1,
                    PRIMARY KEY (permission_id, menu_id)
                )
            """))
            conn.commit()
        print("permission_menus 表创建成功")

    # 检查 permissions 表是否有需要删除的列
    print("检查 permissions 表结构...")
    with engine.connect() as conn:
        # 删除旧的 menu_id 列的 unique 约束（如果存在）
        try:
            conn.execute(text("ALTER TABLE permissions DROP CONSTRAINT IF EXISTS permissions_menu_id_key"))
            conn.commit()
            print("已删除 permissions.menu_id 的 unique 约束")
        except Exception as e:
            print(f"删除约束时：{e}")

    # 删除 permissions 表中不再需要的列
    permissions_columns = [col['name'] for col in inspector.get_columns('permissions')]

    columns_to_drop = ['type', 'api_method', 'api_path', 'menu_id']

    with engine.connect() as conn:
        for col in columns_to_drop:
            if col in permissions_columns:
                print(f"删除 permissions.{col} 列...")
                try:
                    conn.execute(text(f"ALTER TABLE permissions DROP COLUMN {col}"))
                    conn.commit()
                    print(f"已删除列：{col}")
                except Exception as e:
                    print(f"删除列 {col} 时出错：{e}")
            else:
                print(f"列 {col} 不存在，跳过")

    print("\n迁移完成!")

if __name__ == "__main__":
    migrate()
