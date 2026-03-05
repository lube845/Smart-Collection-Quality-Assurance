"""
审计日志服务
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.audit import AuditLog


class AuditService:
    """审计日志服务"""

    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        resource: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        request_url: Optional[str] = None,
        request_body: Optional[dict] = None,
        request_params: Optional[dict] = None,
        response_status: Optional[int] = None,
        response_message: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> AuditLog:
        """记录审计日志"""
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=action,
            resource=resource,
            resource_id=resource_id,
            method=method,
            request_url=request_url,
            request_body=request_body,
            request_params=request_params,
            response_status=response_status,
            response_message=response_message,
            extra=extra,
            created_at=datetime.utcnow(),
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditLog], int]:
        """查询审计日志"""
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        # 统计总数
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 分页
        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    # 常用操作日志
    @staticmethod
    async def log_login(db: AsyncSession, user_id: int, username: str, ip_address: str, success: bool):
        """记录登录日志"""
        await AuditService.log(
            db=db,
            action="login",
            resource="auth",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            response_status=200 if success else 401,
            response_message="登录成功" if success else "登录失败",
        )

    @staticmethod
    async def log_rule_change(db: AsyncSession, user_id: int, username: str, action: str, rule_id: str, ip_address: str):
        """记录规则变更日志"""
        await AuditService.log(
            db=db,
            action=action,
            resource="scoring_rule",
            resource_id=str(rule_id),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_playback(db: AsyncSession, user_id: int, username: str, recording_id: int, ip_address: str):
        """记录录音播放日志"""
        await AuditService.log(
            db=db,
            action="play",
            resource="recording",
            resource_id=str(recording_id),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_download(db: AsyncSession, user_id: int, username: str, recording_id: int, ip_address: str):
        """记录录音下载日志"""
        await AuditService.log(
            db=db,
            action="download",
            resource="recording",
            resource_id=str(recording_id),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_export(db: AsyncSession, user_id: int, username: str, export_type: str, count: int, ip_address: str):
        """记录批量导出日志"""
        await AuditService.log(
            db=db,
            action="export",
            resource=export_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            extra={"count": count},
        )
