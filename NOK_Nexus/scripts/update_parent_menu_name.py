"""
更新市场调研父菜单名称：市场调研 -> 采购管理
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Menu

def update_parent_menu():
    """更新父菜单名称"""
    db = SessionLocal()

    try:
        # 查找市场调研父菜单
        parent_menu = db.query(Menu).filter(Menu.code == "market_research").first()

        if not parent_menu:
            print("未找到市场调研父菜单")
            return

        print(f"找到菜单：{parent_menu.name} (id={parent_menu.id})")

        # 更新菜单名称
        parent_menu.name = "采购管理"

        db.commit()

        print("\n更新完成！")
        print(f"  新名称：{parent_menu.name}")

    except Exception as e:
        db.rollback()
        print(f"更新失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_parent_menu()
