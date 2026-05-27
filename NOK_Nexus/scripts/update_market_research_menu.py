"""
更新市场调研菜单名称：BI 分析 -> 市场调研
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Menu

def update_market_research_menu():
    """更新市场调研菜单名称和路径"""
    db = SessionLocal()

    try:
        # 查找 BI 分析菜单
        analysis_menu = db.query(Menu).filter(Menu.code == "market_research_analysis").first()

        if not analysis_menu:
            print("未找到 BI 分析菜单")
            return

        print(f"找到菜单：{analysis_menu.name} (id={analysis_menu.id})")
        print(f"  原路径：{analysis_menu.path}")
        print(f"  原组件：{analysis_menu.component}")

        # 更新菜单名称
        analysis_menu.name = "市场调研"
        # 更新路径
        analysis_menu.path = "/market-research/research"
        # 更新组件路径
        analysis_menu.component = "market-research/research/page"

        db.commit()

        print("\n更新完成！")
        print(f"  新名称：{analysis_menu.name}")
        print(f"  新路径：{analysis_menu.path}")
        print(f"  新组件：{analysis_menu.component}")

    except Exception as e:
        db.rollback()
        print(f"更新失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_market_research_menu()
