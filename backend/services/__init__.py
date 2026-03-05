"""
服务层
"""
from .auth_service import (
    AuthService,
    verify_password,
    get_password_hash,
    get_current_user,
    get_current_active_super_admin,
    get_current_org_admin,
)
from .oss_service import oss_service, OSSService
from .asr_service import asr_service, ASRService
from .ai_scoring_service import ai_scoring_service, AIScoringService
from .audit_service import AuditService

__all__ = [
    # 认证服务
    "AuthService",
    "verify_password",
    "get_password_hash",
    "get_current_user",
    "get_current_active_super_admin",
    "get_current_org_admin",
    # 对象存储服务
    "oss_service",
    "OSSService",
    # ASR服务
    "asr_service",
    "ASRService",
    # AI评分服务
    "ai_scoring_service",
    "AIScoringService",
    # 审计服务
    "AuditService",
]
