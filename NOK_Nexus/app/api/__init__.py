"""
API 路由初始化
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .menus import router as menus_router
from .permissions import router as permissions_router
from .data_scopes import router as data_scopes_router
from .departments import router as departments_router
from .logs import router as logs_router
from .market_research import router as market_research_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证管理"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(roles_router, prefix="/roles", tags=["角色管理"])
api_router.include_router(menus_router, prefix="/menus", tags=["菜单管理"])
api_router.include_router(
    permissions_router, prefix="/permissions", tags=["权限管理"]
)
api_router.include_router(
    data_scopes_router, prefix="/data-scopes", tags=["数据权限管理"]
)
api_router.include_router(
    departments_router, prefix="/departments", tags=["部门管理"]
)
api_router.include_router(logs_router, prefix="/logs", tags=["日志管理"])
api_router.include_router(
    market_research_router, prefix="/market-research", tags=["市场调研"]
)
