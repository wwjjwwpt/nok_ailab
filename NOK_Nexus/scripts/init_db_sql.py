#!/usr/bin/env python3
"""
数据库初始化脚本 - 使用 SQL 文件

使用方法:
    python scripts/init_db_sql.py
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.config import settings


def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def init_database():
    """使用 SQL 文件初始化数据库"""
    print_header("NOK AI Lab - 数据库初始化 (SQL)")

    print(f"\n数据库配置:")
    print(f"  Host: {settings.DB_HOST}")
    print(f"  Port: {settings.DB_PORT}")
    print(f"  Database: {settings.DB_NAME}")
    print(f"  User: {settings.DB_USER}")

    import psycopg2

    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        conn.autocommit = False
        cur = conn.cursor()

        print("✅ 数据库连接成功!")

        # 读取 SQL 文件
        sql_file = os.path.join(os.path.dirname(__file__), 'init_full.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print(f"\n正在执行 SQL 脚本...")

        # 执行 SQL
        cur.execute(sql_content)
        conn.commit()

        print("✅ SQL 脚本执行成功!")

        # 显示结果
        cur.execute("""
            SELECT '初始化完成!' AS status,
                   (SELECT COUNT(*) FROM users) AS users_count,
                   (SELECT COUNT(*) FROM roles) AS roles_count,
                   (SELECT COUNT(*) FROM menus) AS menus_count,
                   (SELECT COUNT(*) FROM permissions) AS permissions_count,
                   (SELECT COUNT(*) FROM departments) AS departments_count
        """)
        result = cur.fetchone()
        print(f"\n📊 数据统计:")
        print(f"  用户数：   {result[1]}")
        print(f"  角色数：   {result[2]}")
        print(f"  菜单数：   {result[3]}")
        print(f"  权限数：   {result[4]}")
        print(f"  部门数：   {result[5]}")

        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成!")
        print("=" * 60)
        print("\n🔐 默认账号:")
        print("  用户名：admin")
        print("  密码：admin123")
        print("\n下一步:")
        print("  1. 启动后端：cd backend && uvicorn app.main:app --reload")
        print("  2. 启动前端：cd frontend && npm run dev")
        print("  3. 访问系统：http://localhost:3000")

        return True

    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
