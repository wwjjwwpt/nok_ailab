"""
初始化市场调研菜单、权限和采购主管角色
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models import (
    Menu, Permission, Role, RoleMenu, RolePermission,
    PermissionMenu, User, UserRole
)
from app.core.security import get_password_hash

def init_market_research_menu():
    """初始化市场调研菜单和权限"""
    db = SessionLocal()

    try:
        # 检查是否已存在市场调研菜单
        existing_menu = db.query(Menu).filter(Menu.code == "market_research").first()
        if existing_menu:
            print("市场调研菜单已存在，跳过初始化")
            return

        print("开始初始化市场调研菜单和权限...")

        # ==================== 1. 创建市场调研父菜单 ====================
        market_research_menu = Menu(
            name="市场调研",
            code="market_research",
            parent_id=0,
            path="/market-research",
            component="layout",
            icon="PieChart",
            type=1,  # 目录
            sort_order=50,
            visible=True,
            status=1,
        )
        db.add(market_research_menu)
        db.flush()
        print(f"创建父菜单：市场调研 (id={market_research_menu.id})")

        # ==================== 2. 创建子菜单 ====================
        # 调研数据列表
        list_menu = Menu(
            name="调研数据",
            code="market_research_list",
            parent_id=market_research_menu.id,
            path="/market-research/list",
            component="market-research/list/page",
            icon="Table",
            type=2,  # 菜单
            sort_order=1,
            visible=True,
            status=1,
        )
        db.add(list_menu)
        db.flush()
        print(f"创建子菜单：调研数据 (id={list_menu.id})")

        # BI 分析看板
        analysis_menu = Menu(
            name="BI 分析",
            code="market_research_analysis",
            parent_id=market_research_menu.id,
            path="/market-research/analysis",
            component="market-research/analysis/page",
            icon="Dashboard",
            type=2,  # 菜单
            sort_order=2,
            visible=True,
            status=1,
        )
        db.add(analysis_menu)
        db.flush()
        print(f"创建子菜单：BI 分析 (id={analysis_menu.id})")

        # ==================== 3. 创建功能权限 ====================
        permissions_data = [
            ("查看调研数据", "market_research:view", list_menu.id),
            ("创建调研数据", "market_research:create", list_menu.id),
            ("编辑调研数据", "market_research:edit", list_menu.id),
            ("删除调研数据", "market_research:delete", list_menu.id),
            ("查看 BI 分析", "market_research:analyze", analysis_menu.id),
        ]

        permission_ids = []
        for perm_info in permissions_data:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                description=f"{perm_info[0]}权限",
                status=1,
            )
            db.add(perm)
            db.flush()

            # 关联权限到菜单
            perm_menu = PermissionMenu(permission_id=perm.id, menu_id=perm_info[2], status=1)
            db.add(perm_menu)

            permission_ids.append(perm.id)
            print(f"创建权限：{perm_info[0]} ({perm_info[1]}) -> 菜单 ID={perm_info[2]}")

        # ==================== 4. 创建采购主管角色 ====================
        # 检查是否已存在
        purchase_role = db.query(Role).filter(Role.code == "purchase_supervisor").first()
        if not purchase_role:
            purchase_role = Role(
                name="采购主管",
                code="purchase_supervisor",
                description="负责市场调研和采购决策的主管角色",
                is_system=False,
                status=1,
            )
            db.add(purchase_role)
            db.flush()
            print(f"创建角色：采购主管 (id={purchase_role.id})")
        else:
            print(f"角色已存在：采购主管 (id={purchase_role.id})")

        # ==================== 5. 为采购主管角色分配菜单 ====================
        # 分配父菜单
        db.add(RoleMenu(role_id=purchase_role.id, menu_id=market_research_menu.id, status=1))
        # 分配子菜单
        db.add(RoleMenu(role_id=purchase_role.id, menu_id=list_menu.id, status=1))
        db.add(RoleMenu(role_id=purchase_role.id, menu_id=analysis_menu.id, status=1))
        print("已为采购主管角色分配菜单权限")

        # ==================== 6. 为采购主管角色分配功能权限 ====================
        for perm_id in permission_ids:
            db.add(RolePermission(role_id=purchase_role.id, permission_id=perm_id, status=1))
        print("已为采购主管角色分配功能权限")

        # ==================== 7. 创建测试用户（可选） ====================
        test_user = db.query(User).filter(User.username == "purchase_user").first()
        if not test_user:
            test_user = User(
                username="purchase_user",
                password=get_password_hash("purchase123"),
                email="purchase@example.com",
                nickname="采购员",
                status=1,
                email_verified=True,
            )
            db.add(test_user)
            db.flush()

            # 关联采购主管角色
            db.add(UserRole(user_id=test_user.id, role_id=purchase_role.id, status=1))
            print("创建测试用户：purchase_user / purchase123")

        db.commit()
        print("\n市场调研菜单、权限和角色初始化完成！")
        print("\n测试账号:")
        print("  用户名：purchase_user")
        print("  密码：purchase123")
        print("  角色：采购主管")

    except Exception as e:
        db.rollback()
        print(f"初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_market_research_menu()
