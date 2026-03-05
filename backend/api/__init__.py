"""
API路由
"""
from .auth import router as auth_router, user_router, org_router
from .recording import router as recording_router
from .rule import router as rule_router
from .app import app_group_router, stats_router, export_router

__all__ = [
    "auth_router",
    "user_router",
    "org_router",
    "recording_router",
    "rule_router",
    "app_group_router",
    "stats_router",
    "export_router",
]
