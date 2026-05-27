"""
权限服务
处理菜单权限、功能权限、数据权限的计算
"""
from typing import List, Set, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models import (
    User,
    Role,
    Permission,
    Menu,
    DataScope,
    UserRole,
    RolePermission,
    RoleMenu,
    RoleDataScope,
    UserPermission,
    UserDataSource,
    Department,
    RoleHierarchy,
)


class PermissionService:
    """权限服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 菜单权限 ====================

    async def get_user_menu_ids(self, user_id: int) -> Set[int]:
        """获取用户可访问的菜单 ID 集合 - 支持角色层级继承和用户直接权限"""
        menu_ids = set()

        # 1. 通过角色获取菜单权限
        role_ids = (
            self.db.query(UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        role_ids = [r[0] for r in role_ids]

        if role_ids:
            # 递归获取所有父角色 ID（父角色继承子角色权限）
            all_role_ids = self._get_all_role_ids(role_ids)

            # 查询角色关联的菜单
            role_menu_ids = (
                self.db.query(RoleMenu.menu_id)
                .filter(RoleMenu.role_id.in_(all_role_ids))
                .all()
            )
            menu_ids.update(m[0] for m in role_menu_ids)

        # 2. 通过用户直接权限获取菜单权限
        # 查询用户直接权限
        user_perm_ids = (
            self.db.query(UserPermission.permission_id)
            .filter(UserPermission.user_id == user_id, UserPermission.grant_type == 1)
            .all()
        )
        user_perm_ids = [p[0] for p in user_perm_ids]

        if user_perm_ids:
            # 通过 permission_menus 表获取权限关联的菜单
            perm_menu_ids = (
                self.db.query(PermissionMenu.menu_id)
                .filter(PermissionMenu.permission_id.in_(user_perm_ids))
                .all()
            )
            menu_ids.update(m[0] for m in perm_menu_ids)

        # 3. 递归获取父菜单 (确保能访问到顶级)
        menu_ids = self._get_menu_with_parents(menu_ids)

        return menu_ids

    def _get_menu_with_parents(self, menu_ids: Set[int]) -> Set[int]:
        """递归获取所有父菜单 ID"""
        result = set(menu_ids)
        changed = True

        while changed:
            changed = False
            menus = (
                self.db.query(Menu)
                .filter(Menu.id.in_(result), Menu.parent_id > 0)
                .all()
            )

            for menu in menus:
                if menu.parent_id not in result:
                    result.add(menu.parent_id)
                    changed = True

        return result

    async def get_user_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可访问的菜单树"""
        menu_ids = await self.get_user_menu_ids(user_id)

        if not menu_ids:
            return []

        # 查询菜单
        menus = (
            self.db.query(Menu)
            .filter(Menu.id.in_(menu_ids), Menu.visible == True)
            .order_by(Menu.sort_order, Menu.id)
            .all()
        )

        # 构建树形结构
        return self._build_menu_tree(menus)

    def _build_menu_tree(self, menus: List[Menu]) -> List[Dict[str, Any]]:
        """构建菜单树"""

        def menu_to_dict(menu: Menu) -> Dict[str, Any]:
            return {
                "id": menu.id,
                "name": menu.name,
                "code": menu.code,
                "parent_id": menu.parent_id,
                "path": menu.path,
                "component": menu.component,
                "icon": menu.icon,
                "type": menu.type,
                "sort_order": menu.sort_order,
                "visible": menu.visible,
                "permission": menu.permission,
                "children": [],
            }

        # 转为字典
        menu_dict = {menu.id: menu_to_dict(menu) for menu in menus}

        # 构建树
        result = []
        for menu_id, menu_data in menu_dict.items():
            parent_id = menu_data["parent_id"]
            if parent_id == 0 or parent_id not in menu_dict:
                result.append(menu_data)
            else:
                menu_dict[parent_id]["children"].append(menu_data)

        return result

    # ==================== 功能权限 ====================

    def _get_all_role_ids(self, role_ids: List[int]) -> Set[int]:
        """递归获取所有角色 ID（包括父角色）- 父角色继承子角色的权限"""
        all_role_ids = set(role_ids)
        changed = True

        while changed:
            changed = False
            # 查询这些角色作为子角色的父角色
            parent_roles = (
                self.db.query(RoleHierarchy.parent_role_id)
                .filter(
                    RoleHierarchy.child_role_id.in_(all_role_ids),
                    RoleHierarchy.status == 1
                )
                .all()
            )
            parent_ids = set(pr[0] for pr in parent_roles)
            for pid in parent_ids:
                if pid not in all_role_ids:
                    all_role_ids.add(pid)
                    changed = True

        return all_role_ids

    async def get_user_permission_codes(self, user_id: int) -> Set[str]:
        """获取用户所有权限码 - 支持角色层级继承"""
        permissions = set()

        # 1. 获取用户的角色
        role_ids = (
            self.db.query(UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        role_ids = [r[0] for r in role_ids]

        if role_ids:
            # 递归获取所有父角色 ID（父角色继承子角色权限）
            all_role_ids = self._get_all_role_ids(role_ids)

            # 查询角色的权限
            perm_ids = (
                self.db.query(RolePermission.permission_id)
                .filter(RolePermission.role_id.in_(all_role_ids))
                .all()
            )
            perm_ids = [p[0] for p in perm_ids]

            if perm_ids:
                perms = self.db.query(Permission.code).filter(
                    Permission.id.in_(perm_ids)
                ).all()
                permissions.update(p[0] for p in perms)

        # 2. 获取用户直接权限 (允许)
        user_perms = (
            self.db.query(UserPermission)
            .filter(UserPermission.user_id == user_id, UserPermission.grant_type == 1)
            .all()
        )
        for up in user_perms:
            perm = self.db.query(Permission.code).filter(Permission.id == up.permission_id).first()
            if perm:
                permissions.add(perm[0])

        # 3. 减去拒绝的权限
        deny_perms = (
            self.db.query(UserPermission)
            .filter(UserPermission.user_id == user_id, UserPermission.grant_type == 2)
            .all()
        )
        for dp in deny_perms:
            perm = self.db.query(Permission.code).filter(Permission.id == dp.permission_id).first()
            if perm:
                permissions.discard(perm[0])

        return permissions

    async def check_user_permission(
        self, user_id: int, permission_code: str
    ) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = await self.get_user_permission_codes(user_id)
        return permission_code in user_permissions

    # ==================== 数据权限 ====================

    async def get_user_data_scopes(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的数据权限范围 - 支持角色层级继承"""
        data_scopes = []

        # 1. 获取用户的角色
        role_ids = (
            self.db.query(UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        role_ids = [r[0] for r in role_ids]

        if role_ids:
            # 递归获取所有父角色 ID
            all_role_ids = self._get_all_role_ids(role_ids)

            # 获取角色的数据权限
            scope_ids = (
                self.db.query(RoleDataScope.data_scope_id)
                .filter(RoleDataScope.role_id.in_(all_role_ids))
                .all()
            )
            scope_ids = [s[0] for s in scope_ids]

            if scope_ids:
                scopes = self.db.query(DataScope).filter(
                    DataScope.id.in_(scope_ids)
                ).all()
                data_scopes.extend(
                    {"scope_type": s.scope_type, "scope_config": s.scope_config}
                    for s in scopes
                )

        # 2. 获取用户直接数据权限
        user_scope_ids = (
            self.db.query(UserDataSource.data_scope_id)
            .filter(UserDataSource.user_id == user_id)
            .all()
        )
        user_scope_ids = [s[0] for s in user_scope_ids]

        if user_scope_ids:
            scopes = self.db.query(DataScope).filter(
                DataScope.id.in_(user_scope_ids)
            ).all()
            data_scopes.extend(
                {"scope_type": s.scope_type, "scope_config": s.scope_config}
                for s in scopes
            )

        return data_scopes

    def build_data_scope_filter(
        self, user_id: int, dept_column: str = "dept_id"
    ) -> Any:
        """
        构建数据权限 SQL 过滤条件
        :param user_id: 用户 ID
        :param dept_column: 部门字段名
        :return: SQLAlchemy 过滤条件
        """
        # 获取用户信息
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return and_(False)  # 用户不存在，返回空结果

        # 获取数据权限
        data_scopes = self.db.query(DataScope.scope_type).join(
            RoleDataScope, DataScope.id == RoleDataScope.data_scope_id
        ).join(
            UserRole, UserRole.role_id == RoleDataScope.role_id
        ).filter(
            UserRole.user_id == user_id
        ).all()

        if not data_scopes:
            # 无权限，默认只查自己的数据
            return getattr(self.db.class_, dept_column) == user.dept_id

        scope_types = set(s[0] for s in data_scopes)

        # 1-全部数据
        if 1 in scope_types:
            return None  # 不过滤

        # 构建过滤条件
        conditions = []

        # 2-本部门及子部门
        if 2 in scope_types:
            child_depts = self._get_dept_children(user.dept_id)
            conditions.append(getattr(User, dept_column).in_(child_depts))

        # 3-本部门
        if 3 in scope_types:
            conditions.append(getattr(User, dept_column) == user.dept_id)

        # 4-本人
        if 4 in scope_types:
            conditions.append(User.id == user_id)

        # 5-自定义 (需要额外查询配置)
        if 5 in scope_types:
            custom_scopes = self.db.query(DataScope.scope_config).filter(
                DataScope.scope_type == 5
            ).join(
                RoleDataScope, DataScope.id == RoleDataScope.data_scope_id
            ).join(
                UserRole, UserRole.role_id == RoleDataScope.role_id
            ).filter(
                UserRole.user_id == user_id
            ).all()

            for scope in custom_scopes:
                if scope.scope_config and "dept_ids" in scope.scope_config:
                    conditions.append(
                        getattr(User, dept_column).in_(scope.scope_config["dept_ids"])
                    )

        return or_(*conditions) if conditions else and_(False)

    def _get_dept_children(self, dept_id: int) -> List[int]:
        """递归获取部门及所有子部门 ID"""
        result = {dept_id}
        children = (
            self.db.query(Department.id)
            .filter(Department.parent_id == dept_id)
            .all()
        )

        for child in children:
            result.update(self._get_dept_children(child[0]))

        return list(result)
