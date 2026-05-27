#!/usr/bin/env python3
"""
nok_admin 角色初始化脚本
创建角色层级结构:
- nok_admin (父角色)
  ├── user_admin (子角色) - 用户管理权限
  ├── role_admin (子角色) - 角色管理权限
  └── dept_admin (子角色) - 部门管理权限

父角色自动继承所有子角色的权限
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.database import get_db
from app.models import (
    Role, Menu, Permission, RoleHierarchy,
    RolePermission, RoleMenu, UserRole, User
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def init_nok_admin_roles():
    """创建 nok_admin 角色体系"""
    print_header("NOK AI Lab - nok_admin 角色初始化")

    db = next(get_db())

    try:
        # ==================== 1. 创建角色 ====================
        print("\n📋 创建角色...")

        # 创建父角色 nok_admin
        nok_admin = db.query(Role).filter(Role.code == "nok_admin").first()
        if not nok_admin:
            nok_admin = Role(
                name="nok_admin",
                code="nok_admin",
                description="NOK AI Lab 超级管理员",
                is_system=True,
                status=1
            )
            db.add(nok_admin)
            db.commit()
            db.refresh(nok_admin)
            print(f"  ✅ 创建父角色：nok_admin (ID={nok_admin.id})")
        else:
            print(f"  ⚠️  角色已存在：nok_admin (ID={nok_admin.id})")

        # 创建子角色 - user_admin
        user_admin = db.query(Role).filter(Role.code == "user_admin").first()
        if not user_admin:
            user_admin = Role(
                name="user_admin",
                code="user_admin",
                description="用户管理员 - 管理用户和用户角色分配",
                is_system=True,
                status=1
            )
            db.add(user_admin)
            db.commit()
            db.refresh(user_admin)
            print(f"  ✅ 创建子角色：user_admin (ID={user_admin.id})")
        else:
            print(f"  ⚠️  角色已存在：user_admin (ID={user_admin.id})")

        # 创建子角色 - role_admin
        role_admin = db.query(Role).filter(Role.code == "role_admin").first()
        if not role_admin:
            role_admin = Role(
                name="role_admin",
                code="role_admin",
                description="角色管理员 - 管理角色和权限分配",
                is_system=True,
                status=1
            )
            db.add(role_admin)
            db.commit()
            db.refresh(role_admin)
            print(f"  ✅ 创建子角色：role_admin (ID={role_admin.id})")
        else:
            print(f"  ⚠️  角色已存在：role_admin (ID={role_admin.id})")

        # 创建子角色 - dept_admin
        dept_admin = db.query(Role).filter(Role.code == "dept_admin").first()
        if not dept_admin:
            dept_admin = Role(
                name="dept_admin",
                code="dept_admin",
                description="部门管理员 - 管理部门和数据权限",
                is_system=True,
                status=1
            )
            db.add(dept_admin)
            db.commit()
            db.refresh(dept_admin)
            print(f"  ✅ 创建子角色：dept_admin (ID={dept_admin.id})")
        else:
            print(f"  ⚠️  角色已存在：dept_admin (ID={dept_admin.id})")

        # ==================== 2. 建立角色层级关系 ====================
        print("\n🔗 建立角色层级关系...")

        # user_admin -> nok_admin (nok_admin 继承 user_admin 的权限)
        for child_role in [user_admin, role_admin, dept_admin]:
            existing = db.query(RoleHierarchy).filter(
                RoleHierarchy.parent_role_id == nok_admin.id,
                RoleHierarchy.child_role_id == child_role.id
            ).first()
            if not existing:
                hierarchy = RoleHierarchy(
                    parent_role_id=nok_admin.id,
                    child_role_id=child_role.id,
                    status=1
                )
                db.add(hierarchy)
                print(f"  ✅ 建立层级：nok_admin ← {child_role.code}")

        db.commit()
        print("  ✅ 角色层级关系建立完成")

        # ==================== 3. 创建权限 ====================
        print("\n🔐 创建权限...")

        # 用户管理权限
        user_perms = [
            {"name": "查看用户", "code": "user:view", "type": "api", "api_method": "GET", "api_path": "/api/v1/users"},
            {"name": "创建用户", "code": "user:add", "type": "api", "api_method": "POST", "api_path": "/api/v1/users"},
            {"name": "编辑用户", "code": "user:edit", "type": "api", "api_method": "PUT", "api_path": "/api/v1/users/{id}"},
            {"name": "删除用户", "code": "user:delete", "type": "api", "api_method": "DELETE", "api_path": "/api/v1/users/{id}"},
            {"name": "分配角色", "code": "user:assign_roles", "type": "api", "api_method": "POST", "api_path": "/api/v1/users/{id}/roles"},
        ]

        # 角色管理权限
        role_perms = [
            {"name": "查看角色", "code": "role:view", "type": "api", "api_method": "GET", "api_path": "/api/v1/roles"},
            {"name": "创建角色", "code": "role:add", "type": "api", "api_method": "POST", "api_path": "/api/v1/roles"},
            {"name": "编辑角色", "code": "role:edit", "type": "api", "api_method": "PUT", "api_path": "/api/v1/roles/{id}"},
            {"name": "删除角色", "code": "role:delete", "type": "api", "api_method": "DELETE", "api_path": "/api/v1/roles/{id}"},
            {"name": "分配权限", "code": "role:assign_perms", "type": "api", "api_method": "POST", "api_path": "/api/v1/roles/{id}/permissions"},
        ]

        # 部门管理权限
        dept_perms = [
            {"name": "查看部门", "code": "dept:view", "type": "api", "api_method": "GET", "api_path": "/api/v1/departments"},
            {"name": "创建部门", "code": "dept:add", "type": "api", "api_method": "POST", "api_path": "/api/v1/departments"},
            {"name": "编辑部门", "code": "dept:edit", "type": "api", "api_method": "PUT", "api_path": "/api/v1/departments/{id}"},
            {"name": "删除部门", "code": "dept:delete", "type": "api", "api_method": "DELETE", "api_path": "/api/v1/departments/{id}"},
        ]

        # 菜单管理权限
        menu_perms = [
            {"name": "查看菜单", "code": "menu:view", "type": "api", "api_method": "GET", "api_path": "/api/v1/menus"},
            {"name": "创建菜单", "code": "menu:add", "type": "api", "api_method": "POST", "api_path": "/api/v1/menus"},
            {"name": "编辑菜单", "code": "menu:edit", "type": "api", "api_method": "PUT", "api_path": "/api/v1/menus/{id}"},
            {"name": "删除菜单", "code": "menu:delete", "type": "api", "api_method": "DELETE", "api_path": "/api/v1/menus/{id}"},
        ]

        # 数据权限管理
        data_scope_perms = [
            {"name": "查看数据权限", "code": "data_scope:view", "type": "api", "api_method": "GET", "api_path": "/api/v1/data-scopes"},
            {"name": "创建数据权限", "code": "data_scope:add", "type": "api", "api_method": "POST", "api_path": "/api/v1/data-scopes"},
            {"name": "编辑数据权限", "code": "data_scope:edit", "type": "api", "api_method": "PUT", "api_path": "/api/v1/data-scopes/{id}"},
            {"name": "删除数据权限", "code": "data_scope:delete", "type": "api", "api_method": "DELETE", "api_path": "/api/v1/data-scopes/{id}"},
        ]

        all_perms = {
            "user_admin": user_perms,
            "role_admin": role_perms + menu_perms,
            "dept_admin": dept_perms + data_scope_perms,
        }

        # 获取系统管理菜单 ID
        system_menu = db.query(Menu).filter(Menu.code == "system").first()
        if not system_menu:
            system_menu = Menu(
                name="系统管理",
                code="system",
                parent_id=0,
                type=1,
                sort_order=100,
                visible=True,
                status=1
            )
            db.add(system_menu)
            db.commit()
            db.refresh(system_menu)

        # 为每个子角色创建权限并关联菜单
        for role_code, perms in all_perms.items():
            role = db.query(Role).filter(Role.code == role_code).first()
            print(f"\n  📝 为角色 [{role_code}] 创建权限:")

            for perm_data in perms:
                # 检查权限是否已存在
                existing = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
                if not existing:
                    perm = Permission(
                        name=perm_data["name"],
                        code=perm_data["code"],
                        menu_id=system_menu.id,
                        type=perm_data["type"],
                        api_method=perm_data["api_method"],
                        api_path=perm_data["api_path"],
                        status=1
                    )
                    db.add(perm)
                    db.commit()
                    db.refresh(perm)
                    print(f"    ✅ 创建权限：{perm_data['code']} (ID={perm.id})")

                    # 关联权限到角色
                    role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                    db.add(role_perm)
                else:
                    print(f"    ⚠️  权限已存在：{perm_data['code']} (ID={existing.id})")

        db.commit()

        # ==================== 4. 为 nok_admin 分配菜单权限 ====================
        print("\n📋 为 nok_admin 分配菜单权限...")

        # 获取所有系统管理相关菜单
        system_menus = db.query(Menu).filter(
            Menu.code.in_(["system", "user", "role", "menu", "permission", "dept", "data-scope", "log"])
        ).all()

        for menu in system_menus:
            # 使用 raw SQL 检查是否存在
            from sqlalchemy import text
            existing = db.execute(
                text("SELECT 1 FROM role_menus WHERE role_id = :role_id AND menu_id = :menu_id"),
                {"role_id": nok_admin.id, "menu_id": menu.id}
            ).first()
            if not existing:
                role_menu = RoleMenu(role_id=nok_admin.id, menu_id=menu.id)
                db.add(role_menu)

        db.commit()
        print("  ✅ nok_admin 菜单权限分配完成")

        # ==================== 5. 显示最终结果 ====================
        print("\n" + "=" * 60)
        print("🎉 nok_admin 角色体系初始化完成!")
        print("=" * 60)

        print("\n📊 角色层级结构:")
        print("""
        nok_admin (父角色 - 超级管理员)
        ├── user_admin (子角色 - 用户管理权限)
        ├── role_admin (子角色 - 角色/菜单管理权限)
        └── dept_admin (子角色 - 部门/数据权限管理权限)
        """)

        print("📝 权限分配:")
        print("  - nok_admin: 自动继承所有子角色权限 + 所有系统菜单")
        print("  - user_admin: user:view, user:add, user:edit, user:delete, user:assign_roles")
        print("  - role_admin: role:* + menu:* 权限")
        print("  - dept_admin: dept:* + data_scope:* 权限")

        print("\n🔐 默认账号:")
        print("  用户名：admin")
        print("  密码：admin123")
        print("  角色：nok_admin (自动拥有所有子角色权限)")

        print("\n下一步:")
        print("  1. 重启后端服务以加载新的权限服务")
        print("  2. 使用 admin 账号登录测试权限继承")
        print("  3. 创建新用户并分配子角色测试权限隔离")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = init_nok_admin_roles()
    sys.exit(0 if success else 1)
