#!/usr/bin/env python3
"""
数据库初始化脚本
从 .env 读取配置，初始化数据库表和基础数据

使用方法:
    python scripts/init_db.py
"""
import sys
import os

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.database import engine, get_db
from app.core.security import get_password_hash
from sqlalchemy import text


def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def init_database():
    """初始化数据库"""
    print_header("NOK AI Lab - 数据库初始化")

    print("\n正在创建数据库表...")

    # 导入模型 (在创建表之前导入，确保所有模型都注册到 Base)
    from app.models import User, Role, Menu, Permission, DataScope, Department

    # 创建所有表
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功!")

    # 验证表已创建
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"\n已创建 {len(tables)} 张表:")
        for t in tables:
            print(f"  - {t}")


def init_data():
    """初始化基础数据"""
    print_header("初始化基础数据")

    from sqlalchemy.orm import Session
    from app.models import Department, Role, DataScope, Menu, Permission, User, UserRole, RoleMenu, RolePermission, RoleDataScope

    db = Session(bind=engine)

    try:
        # 1. 创建默认部门
        if db.query(Department).count() == 0:
            dept = Department(
                id=1,
                name="默认部门",
                parent_id=0,
                full_path="/1/",
                sort_order=0
            )
            db.add(dept)
            print("✓ 创建默认部门")

        # 2. 创建系统角色
        if db.query(Role).count() == 0:
            roles = [
                Role(id=1, name="超级管理员", code="admin", description="系统超级管理员，拥有所有权限", is_system=True),
                Role(id=2, name="普通用户", code="user", description="普通用户，基础权限", is_system=True),
            ]
            for role in roles:
                db.add(role)
            print("✓ 创建系统角色")

        # 3. 创建数据权限规则
        if db.query(DataScope).count() == 0:
            scopes = [
                DataScope(id=1, name="全部数据", code="all", scope_type=1, description="可访问全部数据"),
                DataScope(id=2, name="本部门及子部门", code="dept_and_children", scope_type=2, description="可访问本部门及下级部门数据"),
                DataScope(id=3, name="本部门", code="dept", scope_type=3, description="仅访问本部门数据"),
                DataScope(id=4, name="仅本人", code="self", scope_type=4, description="仅访问本人创建的数据"),
            ]
            for scope in scopes:
                db.add(scope)
            print("✓ 创建数据权限规则")

        db.commit()

        # 4. 创建菜单
        if db.query(Menu).count() == 0:
            # 一级菜单
            menus = [
                Menu(id=1, name="系统管理", code="system", parent_id=0, path="/system", icon="Settings", type=1, sort_order=100, visible=True),
                # 二级菜单
                Menu(id=10, name="用户管理", code="system_user", parent_id=1, path="/system/user", component="system/user/index", icon="User", type=2, sort_order=1, visible=True),
                Menu(id=11, name="角色管理", code="system_role", parent_id=1, path="/system/role", component="system/role/index", icon="Users", type=2, sort_order=2, visible=True),
                Menu(id=12, name="菜单管理", code="system_menu", parent_id=1, path="/system/menu", component="system/menu/index", icon="Menu", type=2, sort_order=3, visible=True),
                Menu(id=13, name="部门管理", code="system_dept", parent_id=1, path="/system/dept", component="system/dept/index", icon="Users", type=2, sort_order=4, visible=True),
                Menu(id=14, name="权限管理", code="system_perm", parent_id=1, path="/system/permission", component="system/permission/index", icon="Lock", type=2, sort_order=5, visible=True),
                Menu(id=15, name="数据权限", code="system_data_scope", parent_id=1, path="/system/data-scope", component="system/data_scope/index", icon="Database", type=2, sort_order=6, visible=True),
                Menu(id=16, name="日志管理", code="system_log", parent_id=1, path="/system/log", component="system/log/index", icon="FileText", type=2, sort_order=7, visible=True),
            ]
            for menu in menus:
                db.add(menu)
            print("✓ 创建系统菜单")
            db.commit()

        # 5. 创建功能权限
        if db.query(Permission).count() == 0:
            perms = [
                # 用户管理
                Permission(id=101, name="查看用户", code="user:view", menu_id=10, type="button", api_method="GET", api_path="/api/v1/users"),
                Permission(id=102, name="新增用户", code="user:add", menu_id=10, type="button", api_method="POST", api_path="/api/v1/users"),
                Permission(id=103, name="编辑用户", code="user:edit", menu_id=10, type="button", api_method="PUT", api_path="/api/v1/users/*"),
                Permission(id=104, name="删除用户", code="user:delete", menu_id=10, type="button", api_method="DELETE", api_path="/api/v1/users/*"),
                # 角色管理
                Permission(id=201, name="查看角色", code="role:view", menu_id=11, type="button", api_method="GET", api_path="/api/v1/roles"),
                Permission(id=202, name="新增角色", code="role:add", menu_id=11, type="button", api_method="POST", api_path="/api/v1/roles"),
                Permission(id=203, name="编辑角色", code="role:edit", menu_id=11, type="button", api_method="PUT", api_path="/api/v1/roles/*"),
                Permission(id=204, name="删除角色", code="role:delete", menu_id=11, type="button", api_method="DELETE", api_path="/api/v1/roles/*"),
                # 菜单管理
                Permission(id=301, name="查看菜单", code="menu:view", menu_id=12, type="button", api_method="GET", api_path="/api/v1/menus"),
                Permission(id=302, name="新增菜单", code="menu:add", menu_id=12, type="button", api_method="POST", api_path="/api/v1/menus"),
                Permission(id=303, name="编辑菜单", code="menu:edit", menu_id=12, type="button", api_method="PUT", api_path="/api/v1/menus/*"),
                Permission(id=304, name="删除菜单", code="menu:delete", menu_id=12, type="button", api_method="DELETE", api_path="/api/v1/menus/*"),
                # 部门管理
                Permission(id=401, name="查看部门", code="dept:view", menu_id=13, type="button", api_method="GET", api_path="/api/v1/departments"),
                Permission(id=402, name="新增部门", code="dept:add", menu_id=13, type="button", api_method="POST", api_path="/api/v1/departments"),
                Permission(id=403, name="编辑部门", code="dept:edit", menu_id=13, type="button", api_method="PUT", api_path="/api/v1/departments/*"),
                Permission(id=404, name="删除部门", code="dept:delete", menu_id=13, type="button", api_method="DELETE", api_path="/api/v1/departments/*"),
                # 权限管理
                Permission(id=501, name="查看权限", code="permission:view", menu_id=14, type="button", api_method="GET", api_path="/api/v1/permissions"),
                Permission(id=502, name="新增权限", code="permission:add", menu_id=14, type="button", api_method="POST", api_path="/api/v1/permissions"),
                Permission(id=503, name="编辑权限", code="permission:edit", menu_id=14, type="button", api_method="PUT", api_path="/api/v1/permissions/*"),
                Permission(id=504, name="删除权限", code="permission:delete", menu_id=14, type="button", api_method="DELETE", api_path="/api/v1/permissions/*"),
                # 数据权限
                Permission(id=601, name="查看数据权限", code="data_scope:view", menu_id=15, type="button", api_method="GET", api_path="/api/v1/data-scopes"),
                Permission(id=602, name="新增数据权限", code="data_scope:add", menu_id=15, type="button", api_method="POST", api_path="/api/v1/data-scopes"),
                Permission(id=603, name="编辑数据权限", code="data_scope:edit", menu_id=15, type="button", api_method="PUT", api_path="/api/v1/data-scopes/*"),
                Permission(id=604, name="删除数据权限", code="data_scope:delete", menu_id=15, type="button", api_method="DELETE", api_path="/api/v1/data-scopes/*"),
                # 日志管理
                Permission(id=701, name="查看日志", code="log:view", menu_id=16, type="button", api_method="GET", api_path="/api/v1/logs/*"),
                Permission(id=702, name="导出日志", code="log:export", menu_id=16, type="button", api_method="GET", api_path="/api/v1/logs/*/export"),
            ]
            for perm in perms:
                db.add(perm)
            print("✓ 创建功能权限")
            db.commit()

        # 6. 分配管理员角色菜单和权限
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        if admin_role:
            # 关联所有菜单
            all_menus = db.query(Menu).all()
            for menu in all_menus:
                role_menu = RoleMenu(role_id=admin_role.id, menu_id=menu.id)
                db.merge(role_menu)

            # 关联所有权限
            all_perms = db.query(Permission).all()
            for perm in all_perms:
                role_perm = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.merge(role_perm)

            # 关联数据权限
            all_scope = db.query(DataScope).filter(DataScope.scope_type == 1).first()
            if all_scope:
                role_data_scope = RoleDataScope(role_id=admin_role.id, data_scope_id=all_scope.id)
                db.merge(role_data_scope)

            db.commit()
            print("✓ 分配管理员权限")

        # 7. 创建默认管理员账号
        if db.query(User).filter(User.username == "admin").count() == 0:
            admin = User(
                id=1,
                username="admin",
                password=get_password_hash("admin123"),
                email="admin@example.com",
                nickname="管理员",
                dept_id=1,
                status=1,
                email_verified=True
            )
            db.add(admin)
            db.commit()

            # 分配角色
            user_role = UserRole(user_id=1, role_id=1)
            db.add(user_role)
            db.commit()
            print("✓ 创建默认管理员账号 (admin/admin123)")

        print("\n✅ 基础数据初始化完成!")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败：{e}")
        raise
    finally:
        db.close()


def show_summary():
    """显示初始化结果"""
    print_header("初始化结果")

    from sqlalchemy.orm import Session
    from app.models import User, Role, Menu, Permission, Department, DataScope

    db = Session(bind=engine)
    try:
        print(f"\n📊 数据统计:")
        print(f"  用户数：    {db.query(User).count()}")
        print(f"  角色数：    {db.query(Role).count()}")
        print(f"  菜单数：    {db.query(Menu).count()}")
        print(f"  权限数：    {db.query(Permission).count()}")
        print(f"  部门数：    {db.query(Department).count()}")
        print(f"  数据权限：  {db.query(DataScope).count()}")

        print(f"\n🔐 默认账号:")
        print(f"  用户名：admin")
        print(f"  密码：admin123")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    init_data()
    show_summary()

    print("\n" + "=" * 60)
    print("🎉 数据库初始化完成!")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 启动后端：cd backend && uvicorn app.main:app --reload")
    print("  2. 启动前端：cd frontend && npm run dev")
    print("  3. 访问系统：http://localhost:3000")
