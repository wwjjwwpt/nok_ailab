"""
FastAPI 应用主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import time

from .core.config import settings
from .core.database import Base, engine
from .api import api_router


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL,
)


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="企业级 AI 平台 - 认证与权限管理系统",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)

        duration = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}ms"
        )

        return response

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"全局异常：{exc}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # 健康检查
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}

    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
        # 自动创建数据库表 (生产环境建议使用 alembic 迁移)
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表初始化完成")

        # 创建默认系统角色和菜单
        await init_default_data()

    return app


async def init_default_data():
    """初始化默认数据"""
    from sqlalchemy.orm import Session
    from .models import Role, Menu, Permission, DataScope, Department, UserRole, RoleMenu, RolePermission, RoleDataScope
    from .core.database import SessionLocal

    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(Role).count() > 0:
            logger.info("默认数据已存在，跳过初始化")
            return

        logger.info("开始初始化默认数据...")

        # ==================== 1. 创建系统角色 ====================
        admin_role = Role(
            name="超级管理员",
            code="admin",
            description="系统超级管理员，拥有所有权限",
            is_system=True,
        )
        db.add(admin_role)
        db.flush()

        user_role = Role(
            name="普通用户",
            code="user",
            description="普通用户，基础权限",
            is_system=True,
        )
        db.add(user_role)
        db.flush()

        # ==================== 2. 创建数据权限规则 ====================
        data_scopes = [
            DataScope(
                name="全部数据",
                code="all",
                scope_type=1,
                description="可访问全部数据",
            ),
            DataScope(
                name="本部门及子部门",
                code="dept_and_children",
                scope_type=2,
                description="可访问本部门及下级部门数据",
            ),
            DataScope(
                name="本部门",
                code="dept",
                scope_type=3,
                description="仅访问本部门数据",
            ),
            DataScope(
                name="仅本人",
                code="self",
                scope_type=4,
                description="仅访问本人创建的数据",
            ),
        ]
        for scope in data_scopes:
            db.add(scope)
        db.flush()

        # ==================== 3. 创建默认部门 ====================
        default_dept = Department(
            name="默认部门",
            parent_id=0,
            full_path="/1/",
        )
        db.add(default_dept)
        db.flush()

        # ==================== 4. 创建菜单结构 ====================
        # 系统管理目录
        system_menu = Menu(
            name="系统管理",
            code="system",
            parent_id=0,
            path="/system",
            component="layout",
            icon="setting",
            type=1,  # 目录
            sort_order=100,
        )
        db.add(system_menu)
        db.flush()

        # 用户管理
        user_menu = Menu(
            name="用户管理",
            code="system_user",
            parent_id=system_menu.id,
            path="/system/user",
            component="system/user/page",
            icon="user",
            type=2,  # 菜单
            sort_order=1,
        )
        db.add(user_menu)
        db.flush()

        # 角色管理
        role_menu = Menu(
            name="角色管理",
            code="system_role",
            parent_id=system_menu.id,
            path="/system/role",
            component="system/role/page",
            icon="team",
            type=2,
            sort_order=2,
        )
        db.add(role_menu)
        db.flush()

        # 菜单管理
        menu_mgmt_menu = Menu(
            name="菜单管理",
            code="system_menu",
            parent_id=system_menu.id,
            path="/system/menu",
            component="system/menu/page",
            icon="menu",
            type=2,
            sort_order=3,
        )
        db.add(menu_mgmt_menu)
        db.flush()

        # 权限管理
        permission_menu = Menu(
            name="权限管理",
            code="system_permission",
            parent_id=system_menu.id,
            path="/system/permission",
            component="system/permission/page",
            icon="safety",
            type=2,
            sort_order=4,
        )
        db.add(permission_menu)
        db.flush()

        # 部门管理
        dept_menu = Menu(
            name="部门管理",
            code="system_dept",
            parent_id=system_menu.id,
            path="/system/dept",
            component="system/dept/page",
            icon="apartment",
            type=2,
            sort_order=5,
        )
        db.add(dept_menu)
        db.flush()

        # 数据权限
        data_scope_menu = Menu(
            name="数据权限",
            code="system_data_scope",
            parent_id=system_menu.id,
            path="/system/data-scope",
            component="system/data-scope/page",
            icon="database",
            type=2,
            sort_order=6,
        )
        db.add(data_scope_menu)
        db.flush()

        # 日志管理
        log_menu = Menu(
            name="日志管理",
            code="system_log",
            parent_id=system_menu.id,
            path="/system/log",
            component="system/log/page",
            icon="file-text",
            type=2,
            sort_order=7,
        )
        db.add(log_menu)
        db.flush()

        # 仪表板菜单
        dashboard_menu = Menu(
            name="仪表板",
            code="dashboard",
            parent_id=0,
            path="/dashboard",
            component="dashboard/page",
            icon="dashboard",
            type=2,
            sort_order=1,
        )
        db.add(dashboard_menu)
        db.flush()

        # ==================== 5. 创建功能权限 ====================
        permissions_map = {}

        # 用户管理权限
        for perm_info in [
            ("查看用户", "user:view", user_menu.id, "button", "GET", "/users"),
            ("新增用户", "user:add", user_menu.id, "button", "POST", "/users"),
            ("编辑用户", "user:edit", user_menu.id, "button", "PUT", "/users"),
            ("删除用户", "user:delete", user_menu.id, "button", "DELETE", "/users"),
            ("分配角色", "user:assign_role", user_menu.id, "button", "POST", "/users/{id}/roles"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 角色管理权限
        for perm_info in [
            ("查看角色", "role:view", role_menu.id, "button", "GET", "/roles"),
            ("新增角色", "role:add", role_menu.id, "button", "POST", "/roles"),
            ("编辑角色", "role:edit", role_menu.id, "button", "PUT", "/roles"),
            ("删除角色", "role:delete", role_menu.id, "button", "DELETE", "/roles"),
            ("分配权限", "role:assign_permission", role_menu.id, "button", "POST", "/roles/{id}/permissions"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 菜单管理权限
        for perm_info in [
            ("查看菜单", "menu:view", menu_mgmt_menu.id, "button", "GET", "/menus"),
            ("新增菜单", "menu:add", menu_mgmt_menu.id, "button", "POST", "/menus"),
            ("编辑菜单", "menu:edit", menu_mgmt_menu.id, "button", "PUT", "/menus"),
            ("删除菜单", "menu:delete", menu_mgmt_menu.id, "button", "DELETE", "/menus"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 权限管理权限
        for perm_info in [
            ("查看权限", "permission:view", permission_menu.id, "button", "GET", "/permissions"),
            ("新增权限", "permission:add", permission_menu.id, "button", "POST", "/permissions"),
            ("编辑权限", "permission:edit", permission_menu.id, "button", "PUT", "/permissions"),
            ("删除权限", "permission:delete", permission_menu.id, "button", "DELETE", "/permissions"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 部门管理权限
        for perm_info in [
            ("查看部门", "dept:view", dept_menu.id, "button", "GET", "/departments"),
            ("新增部门", "dept:add", dept_menu.id, "button", "POST", "/departments"),
            ("编辑部门", "dept:edit", dept_menu.id, "button", "PUT", "/departments"),
            ("删除部门", "dept:delete", dept_menu.id, "button", "DELETE", "/departments"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 数据权限权限
        for perm_info in [
            ("查看数据权限", "data_scope:view", data_scope_menu.id, "button", "GET", "/data-scopes"),
            ("新增数据权限", "data_scope:add", data_scope_menu.id, "button", "POST", "/data-scopes"),
            ("编辑数据权限", "data_scope:edit", data_scope_menu.id, "button", "PUT", "/data-scopes"),
            ("删除数据权限", "data_scope:delete", data_scope_menu.id, "button", "DELETE", "/data-scopes"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # 日志管理权限
        for perm_info in [
            ("查看登录日志", "log:view_login", log_menu.id, "button", "GET", "/logs/login"),
            ("查看操作日志", "log:view_operation", log_menu.id, "button", "GET", "/logs/operation"),
        ]:
            perm = Permission(
                name=perm_info[0],
                code=perm_info[1],
                menu_id=perm_info[2],
                type=perm_info[3],
                api_method=perm_info[4],
                api_path=perm_info[5],
            )
            db.add(perm)
            db.flush()
            permissions_map[perm_info[1]] = perm.id

        # ==================== 6. 为超级管理员分配所有菜单和权限 ====================
        all_menus = db.query(Menu).all()
        all_permissions = db.query(Permission).all()

        for menu in all_menus:
            db.add(RoleMenu(role_id=admin_role.id, menu_id=menu.id))

        for perm in all_permissions:
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

        # 为超级管理员分配全部数据权限
        all_data_scope = db.query(DataScope).filter(DataScope.scope_type == 1).first()
        if all_data_scope:
            db.add(RoleDataScope(role_id=admin_role.id, data_scope_id=all_data_scope.id))

        # ==================== 7. 为普通用户分配基础菜单 ====================
        db.add(RoleMenu(role_id=user_role.id, menu_id=dashboard_menu.id))

        # ==================== 8. 创建默认管理员账号 ====================
        from .core.security import get_password_hash
        from .models import User

        admin_user = User(
            username="admin",
            password=get_password_hash("admin123"),
            email="admin@example.com",
            phone=None,
            nickname="管理员",
            dept_id=1,
            status=1,
            email_verified=True,
        )
        db.add(admin_user)
        db.flush()

        # 关联管理员角色
        db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

        db.commit()

        logger.info("默认数据初始化完成!")
        logger.info("默认管理员账号：admin / admin123")
        logger.info(f"已创建 {len(all_menus)} 个菜单，{len(all_permissions)} 个权限")

    except Exception as e:
        db.rollback()
        logger.error(f"初始化默认数据失败：{e}")
        raise
    finally:
        db.close()


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
