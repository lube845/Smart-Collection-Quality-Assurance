"""
应用组和统计路由
"""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from io import BytesIO

from ..core.database import get_db
from ..models.user import User, AppGroup
from ..models.recording import Recording, RecordingStatus, RiskLevel
from ..models.rule import ScoringRule
from ..services.auth_service import get_current_user, get_current_org_admin

router = APIRouter(tags=["应用组和统计"])


# ========== 应用组管理 ==========
app_group_router = APIRouter(prefix="/app-groups", tags=["应用组管理"])


@app_group_router.post("")
async def create_app_group(
    name: str = Query(...),
    code: str = Query(...),
    description: Optional[str] = None,
    organization_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建应用组"""
    # 检查代码是否已存在
    result = await db.execute(
        select(AppGroup).where(
            AppGroup.code == code,
            AppGroup.organization_id == organization_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="应用组代码已存在")

    app_group = AppGroup(
        name=name,
        code=code,
        description=description,
        organization_id=organization_id,
    )
    db.add(app_group)
    await db.commit()
    await db.refresh(app_group)

    return app_group


@app_group_router.get("")
async def list_app_groups(
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用组列表"""
    query = select(AppGroup)

    if organization_id:
        query = query.where(AppGroup.organization_id == organization_id)
    elif current_user.organization_id:
        query = query.where(AppGroup.organization_id == current_user.organization_id)

    result = await db.execute(query)
    return result.scalars().all()


@app_group_router.get("/{group_id}")
async def get_app_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用组详情"""
    result = await db.execute(select(AppGroup).where(AppGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="应用组不存在")
    return group


@app_group_router.put("/{group_id}")
async def update_app_group(
    group_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新应用组"""
    result = await db.execute(select(AppGroup).where(AppGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="应用组不存在")

    if name:
        group.name = name
    if description is not None:
        group.description = description
    if is_active is not None:
        group.is_active = is_active

    await db.commit()
    await db.refresh(group)

    return group


# ========== 统计报表 ==========
stats_router = APIRouter(prefix="/statistics", tags=["统计报表"])


@stats_router.get("/overview")
async def get_overview(
    app_group_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据概览"""
    query = select(Recording)

    # 权限过滤
    if current_user.app_group_ids:
        allowed_groups = json.loads(current_user.app_group_ids)
        query = query.where(Recording.app_group_id.in_(allowed_groups))
    elif app_group_id:
        query = query.where(Recording.app_group_id == app_group_id)

    if start_date:
        query = query.where(Recording.call_time >= start_date)
    if end_date:
        query = query.where(Recording.call_time <= end_date)

    # 统计
    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    # 转写中/已完成
    transcribed = await db.scalar(
        select(func.count()).select_from(
            query.where(Recording.status == RecordingStatus.TRANSCRIBED).subquery()
        )
    )

    # 已评分
    scored = await db.scalar(
        select(func.count()).select_from(
            query.where(Recording.status == RecordingStatus.SCORED).subquery()
        )
    )

    # 风险预警
    warnings = await db.scalar(
        select(func.count()).select_from(
            query.where(Recording.risk_level == RiskLevel.DANGER).subquery()
        )
    )

    # 平均分
    avg_score = await db.scalar(
        select(func.avg(Recording.total_score)).select_from(
            query.where(Recording.total_score.isnot(None)).subquery()
        )
    )

    return {
        "total_recordings": total or 0,
        "transcribed": transcribed or 0,
        "scored": scored or 0,
        "warnings": warnings or 0,
        "avg_score": round(avg_score, 2) if avg_score else 0,
    }


@stats_router.get("/score-distribution")
async def get_score_distribution(
    app_group_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分数分布"""
    query = select(Recording.total_score).where(
        Recording.total_score.isnot(None)
    )

    if current_user.app_group_ids:
        allowed_groups = json.loads(current_user.app_group_ids)
        query = query.where(Recording.app_group_id.in_(allowed_groups))
    elif app_group_id:
        query = query.where(Recording.app_group_id == app_group_id)

    if start_date:
        query = query.where(Recording.call_time >= start_date)
    if end_date:
        query = query.where(Recording.call_time <= end_date)

    result = await db.execute(query)
    scores = [s for s in result.scalars().all() if s is not None]

    # 统计分布
    distribution = {
        "0-60": 0,
        "60-70": 0,
        "70-80": 0,
        "80-90": 0,
        "90-100": 0,
    }

    for score in scores:
        if score < 60:
            distribution["0-60"] += 1
        elif score < 70:
            distribution["60-70"] += 1
        elif score < 80:
            distribution["70-80"] += 1
        elif score < 90:
            distribution["80-90"] += 1
        else:
            distribution["90-100"] += 1

    return distribution


@stats_router.get("/agent-rankings")
async def get_agent_rankings(
    app_group_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取坐席排名"""
    query = select(
        Recording.agent_id,
        Recording.agent_name,
        func.count(Recording.id).label("total"),
        func.avg(Recording.total_score).label("avg_score"),
    ).where(
        Recording.agent_id.isnot(None),
        Recording.total_score.isnot(None),
    )

    if current_user.app_group_ids:
        allowed_groups = json.loads(current_user.app_group_ids)
        query = query.where(Recording.app_group_id.in_(allowed_groups))
    elif app_group_id:
        query = query.where(Recording.app_group_id == app_group_id)

    if start_date:
        query = query.where(Recording.call_time >= start_date)
    if end_date:
        query = query.where(Recording.call_time <= end_date)

    query = query.group_by(Recording.agent_id, Recording.agent_name)
    query = query.order_by(func.avg(Recording.total_score).desc())
    query = query.limit(limit)

    result = await db.execute(query)
    rankings = result.all()

    return [
        {
            "agent_id": r.agent_id,
            "agent_name": r.agent_name,
            "total_recordings": r.total,
            "avg_score": round(r.avg_score, 2) if r.avg_score else 0,
        }
        for r in rankings
    ]


# ========== 导出功能 ==========
export_router = APIRouter(prefix="/export", tags=["数据导出"])


@export_router.post("/recordings")
async def export_recordings(
    app_group_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出录音数据到Excel"""
    from openpyxl import Workbook

    query = select(Recording)

    # 权限过滤
    if current_user.app_group_ids:
        allowed_groups = json.loads(current_user.app_group_ids)
        query = query.where(Recording.app_group_id.in_(allowed_groups))
    elif app_group_id:
        query = query.where(Recording.app_group_id == app_group_id)

    if start_date:
        query = query.where(Recording.call_time >= start_date)
    if end_date:
        query = query.where(Recording.call_time <= end_date)
    if status:
        query = query.where(Recording.status == status)

    result = await db.execute(query.order_by(Recording.created_at.desc()))
    recordings = result.scalars().all()

    # 创建Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "录音列表"

    # 表头
    headers = [
        "ID", "文件名", "坐席工号", "坐席姓名", "客户手机号",
        "通话时间", "状态", "风险等级", "总分", "创建时间"
    ]
    ws.append(headers)

    # 数据
    for rec in recordings:
        ws.append([
            rec.id,
            rec.file_name,
            rec.agent_id,
            rec.agent_name,
            rec.customer_phone,
            rec.call_time.strftime("%Y-%m-%d %H:%M:%S") if rec.call_time else "",
            rec.status.value,
            rec.risk_level.value,
            rec.total_score,
            rec.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    # 保存到字节流
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # 记录审计日志
    from ..services.audit_service import AuditService
    await AuditService.log_export(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        export_type="recordings",
        count=len(recordings),
        ip_address="",
    )

    return StreamingResponse(
        output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=recordings_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )
