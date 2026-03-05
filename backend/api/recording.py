"""
录音管理路由
"""
import json
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
import httpx

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..models.recording import Recording, RecordingStatus, RiskLevel, TranscriptSegment, ScoringResult, ScoringDetail
from ..schemas.recording import (
    RecordingUploadInit, RecordingResponse, RecordingDetailResponse,
    RecordingListResponse, ScoringResultResponse, RecordingScoreResponse,
)
from ..services.oss_service import oss_service
from ..services.asr_service import asr_service
from ..services.ai_scoring_service import ai_scoring_service
from ..services.audit_service import AuditService
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/recordings", tags=["录音管理"])


@router.post("/init-upload")
async def init_upload(
    data: RecordingUploadInit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化上传（秒传检查）"""
    # 检查MD5是否已存在（秒传）
    result = await db.execute(
        select(Recording).where(Recording.file_md5 == data.file_md5)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "exists": True,
            "recording_id": existing.id,
            "message": "文件已存在",
        }

    # 生成对象存储键
    object_key = oss_service.generate_object_key(data.file_name, data.app_group_id)

    # 创建录音记录
    recording = Recording(
        file_name=data.file_name,
        file_size=data.file_size,
        file_md5=data.file_md5,
        file_type=data.file_type,
        oss_object_key=object_key,
        oss_bucket=settings.OSS_BUCKET,
        app_group_id=data.app_group_id,
        agent_id=data.agent_id,
        agent_name=data.agent_name,
        customer_id=data.customer_id,
        customer_phone=data.customer_phone,
        call_id=data.call_id,
        call_time=data.call_time,
        status=RecordingStatus.UPLOADING,
        created_by=current_user.id,
    )
    db.add(recording)
    await db.commit()
    await db.refresh(recording)

    return {
        "exists": False,
        "recording_id": recording.id,
        "upload_url": f"/api/v1/recordings/{recording.id}/upload",
        "object_key": object_key,
    }


@router.post("/{recording_id}/upload")
async def upload_file(
    recording_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传录音文件"""
    # 获取录音记录
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音记录不存在")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) != recording.file_size:
        raise HTTPException(status_code=400, detail="文件大小不匹配")

    # 上传到OSS
    try:
        oss_service.upload_file(
            file_data=content,
            object_key=recording.oss_object_key,
            content_type=f"audio/{recording.file_type}",
        )
    except Exception as e:
        recording.status = RecordingStatus.UPLOAD_FAILED
        await db.commit()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

    # 更新录音状态
    recording.status = RecordingStatus.UPLOADED
    await db.commit()

    # 记录审计日志
    await AuditService.log(
        db=db,
        action="upload",
        resource="recording",
        resource_id=str(recording_id),
        user_id=current_user.id,
        username=current_user.username,
        extra={"file_name": recording.file_name},
    )

    # 触发异步转写（通过消息队列或直接调用）
    # 这里直接调用，后续可改为异步任务
    await transcribe_recording(recording_id, db)

    return {"message": "上传成功", "recording_id": recording_id}


async def transcribe_recording(recording_id: int, db: AsyncSession):
    """异步转写录音"""
    # 获取录音记录
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        return

    # 更新状态
    recording.status = RecordingStatus.TRANSCRIBING
    await db.commit()

    try:
        # 获取预签名URL
        oss_url = oss_service.get_presigned_url(recording.oss_object_key)

        # 调用ASR转写
        transcript_result = await asr_service.transcribe_with_role(oss_url)

        # 保存转写结果
        recording.transcript = transcript_result["full_text"]
        recording.transcript_segments = transcript_result["segments"]

        # 保存转写片段
        for seg in transcript_result["segments"]:
            segment = TranscriptSegment(
                recording_id=recording.id,
                speaker=seg["speaker"],
                speaker_name=seg.get("speaker_name"),
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                text=seg["text"],
                confidence=seg.get("confidence"),
            )
            db.add(segment)

        # 更新状态
        recording.status = RecordingStatus.TRANSCRIBED

        # 估算时长（根据转写片段）
        if transcript_result["segments"]:
            last_seg = transcript_result["segments"][-1]
            recording.duration = last_seg["end_time"]

        await db.commit()

    except Exception as e:
        recording.status = RecordingStatus.TRANSCRIBE_FAILED
        recording.remark = f"转写失败: {str(e)}"
        await db.commit()


@router.post("/{recording_id}/transcribe")
async def trigger_transcribe(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发转写"""
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    if recording.status != RecordingStatus.UPLOADED:
        raise HTTPException(status_code=400, detail="录音状态不正确")

    # 触发转写
    await transcribe_recording(recording_id, db)

    return {"message": "转写任务已触发"}


@router.get("", response_model=RecordingListResponse)
async def list_recordings(
    app_group_id: Optional[int] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取录音列表"""
    query = select(Recording)

    # 权限过滤：用户只能看到授权应用组的录音
    if current_user.app_group_ids:
        allowed_groups = json.loads(current_user.app_group_ids)
        query = query.where(Recording.app_group_id.in_(allowed_groups))

    # 条件过滤
    if app_group_id:
        query = query.where(Recording.app_group_id == app_group_id)
    if status:
        query = query.where(Recording.status == status)
    if risk_level:
        query = query.where(Recording.risk_level == risk_level)
    if agent_id:
        query = query.where(Recording.agent_id == agent_id)
    if start_date:
        query = query.where(Recording.call_time >= start_date)
    if end_date:
        query = query.where(Recording.call_time <= end_date)
    if min_score:
        query = query.where(Recording.total_score >= min_score)
    if max_score:
        query = query.where(Recording.total_score <= max_score)
    if keyword:
        query = query.where(
            or_(
                Recording.file_name.ilike(f"%{keyword}%"),
                Recording.agent_name.ilike(f"%{keyword}%"),
                Recording.customer_phone.ilike(f"%{keyword}%"),
            )
        )

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # 分页
    query = query.order_by(Recording.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    recordings = result.scalars().all()

    return RecordingListResponse(
        items=recordings,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{recording_id}", response_model=RecordingDetailResponse)
async def get_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取录音详情"""
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    return recording


@router.get("/{recording_id}/score", response_model=RecordingScoreResponse)
async def get_scoring_result(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取录音评分结果"""
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    # 获取评分结果
    score_result = await db.execute(
        select(ScoringResult)
        .options(selectinload(ScoringResult.details))
        .where(ScoringResult.recording_id == recording_id)
    )
    scoring = score_result.scalar_one_or_none()

    return RecordingScoreResponse(
        recording=recording,
        scoring_result=scoring,
    )


@router.post("/{recording_id}/score")
async def trigger_scoring(
    recording_id: int,
    rule_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发评分"""
    # 获取录音
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    if recording.status != RecordingStatus.TRANSCRIBED:
        raise HTTPException(status_code=400, detail="录音未完成转写")

    # 获取规则
    from ..models.rule import ScoringRule, RuleItem
    if rule_id:
        rule_result = await db.execute(
            select(ScoringRule)
            .options(selectinload(ScoringRule.items))
            .where(ScoringRule.id == rule_id)
        )
        rule = rule_result.scalar_one_or_none()
    else:
        # 获取最新发布的规则
        rule_result = await db.execute(
            select(ScoringRule)
            .options(selectinload(ScoringRule.items))
            .where(
                ScoringRule.organization_id == recording.app_group.organization_id,
                ScoringRule.status == "published",
                ScoringRule.is_latest == True,
            )
            .order_by(ScoringRule.version.desc())
            .limit(1)
        )
        rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="未找到评分规则")

    # 更新状态
    recording.status = RecordingStatus.SCORING
    await db.commit()

    try:
        # 调用AI评分
        scoring_result = await ai_scoring_service.score(
            transcript=recording.transcript or "",
            segments=recording.transcript_segments or [],
            rule=rule,
        )

        # 保存评分结果
        result_record = ScoringResult(
            recording_id=recording.id,
            rule_id=rule.id,
            total_score=scoring_result["total_score"],
            passed=scoring_result["passed"],
            is_rejected=scoring_result["is_rejected"],
            is_auto_scored=True,
            scored_at=datetime.utcnow(),
        )
        db.add(result_record)

        # 保存评分明细
        for detail in scoring_result["details"]:
            scoring_detail = ScoringDetail(
                recording_id=recording.id,
                scoring_result_id=result_record.id,
                rule_item_id=detail["rule_item_id"],
                item_name=detail["item_name"],
                item_type=detail["item_type"],
                status=detail["status"],
                score=detail["score"],
                max_score=detail["max_score"],
                matched_text=detail.get("matched_text"),
                matched_segment_ids=detail.get("matched_segment_ids"),
            )
            db.add(scoring_detail)

        # 更新录音
        recording.status = RecordingStatus.SCORED
        recording.total_score = scoring_result["total_score"]
        recording.rule_version = rule.version
        recording.risk_level = RiskLevel.DANGER if scoring_result["is_rejected"] else RiskLevel.NORMAL

        await db.commit()

        return {
            "message": "评分完成",
            "total_score": scoring_result["total_score"],
            "passed": scoring_result["passed"],
            "is_rejected": scoring_result["is_rejected"],
        }

    except Exception as e:
        recording.status = RecordingStatus.SCORE_FAILED
        recording.remark = f"评分失败: {str(e)}"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")


@router.get("/{recording_id}/play")
async def play_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取录音播放URL（带预签名）"""
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    # 记录审计日志
    await AuditService.log_playback(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        recording_id=recording_id,
        ip_address="",  # 需要从请求中获取
    )

    # 生成预签名URL
    try:
        url = oss_service.get_presigned_url(
            recording.oss_object_key,
            expires=settings.PRESIGNED_URL_EXPIRE,
        )
        return {"play_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成播放URL失败: {str(e)}")


@router.get("/{recording_id}/stream")
async def stream_recording(
    recording_id: int,
    range: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """流式播放录音（HTTP 206）"""
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="录音不存在")

    # 记录审计日志
    await AuditService.log_playback(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        recording_id=recording_id,
        ip_address="",
    )

    # 从OSS获取文件
    try:
        # 这里简化处理，实际应该使用range请求从OSS获取部分内容
        url = oss_service.get_stream_url(recording.oss_object_key)

        # 重定向到OSS URL
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            return StreamingResponse(
                content=response.aiter_bytes(),
                media_type=f"audio/{recording.file_type}",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(recording.file_size),
                },
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音频流失败: {str(e)}")


@router.post("/{recording_id}/rescore")
async def manual_rescore(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新评分（使用最新规则）"""
    return await trigger_scoring(recording_id, None, db, current_user)
