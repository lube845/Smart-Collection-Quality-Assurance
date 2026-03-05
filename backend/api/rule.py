"""
规则管理路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

from ..core.database import get_db
from ..models.user import User
from ..models.rule import ScoringRule, RuleItem, RuleTestRecord, RuleStatus, ItemType
from ..models.recording import Recording
from ..schemas.rule import (
    ScoringRuleCreate, ScoringRuleUpdate, ScoringRuleResponse,
    RuleItemCreate, RuleItemUpdate, RuleItemResponse,
    RuleTestCreate, RuleTestResponse, RulePublishRequest,
)
from ..services.auth_service import get_current_user, get_current_org_admin
from ..services.ai_scoring_service import ai_scoring_service
from ..services.audit_service import AuditService

router = APIRouter(prefix="/rules", tags=["规则管理"])


# ========== 规则项管理 ==========
@router.post("/items", response_model=RuleItemResponse)
async def create_rule_item(
    item_data: RuleItemCreate,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建规则项"""
    # 验证规则存在
    result = await db.execute(select(ScoringRule).where(ScoringRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 检查规则状态
    if rule.status != RuleStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的规则才能添加考核项")

    # 创建规则项
    item = RuleItem(
        rule_id=rule_id,
        name=item_data.name,
        code=item_data.code,
        item_type=ItemType(item_data.item_type),
        max_score=item_data.max_score,
        default_score=item_data.default_score,
        is_deduction=item_data.is_deduction,
        deduction_type=item_data.deduction_type,
        deduction_value=item_data.deduction_value,
        is_required=item_data.is_required,
        is_veto=item_data.is_veto,
        tags=item_data.tags,
        category=item_data.category,
        match_prompt=item_data.match_prompt,
        sort_order=item_data.sort_order,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return item


@router.put("/items/{item_id}", response_model=RuleItemResponse)
async def update_rule_item(
    item_id: int,
    item_data: RuleItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新规则项"""
    result = await db.execute(select(RuleItem).where(RuleItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="规则项不存在")

    # 检查规则状态
    if item.rule.status != RuleStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的规则才能修改")

    # 更新字段
    update_data = item_data.model_dump(exclude_unset=True)
    if "item_type" in update_data:
        update_data["item_type"] = ItemType(update_data["item_type"])

    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    return item


@router.delete("/items/{item_id}")
async def delete_rule_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除规则项"""
    result = await db.execute(select(RuleItem).where(RuleItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="规则项不存在")

    # 检查规则状态
    if item.rule.status != RuleStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的规则才能删除")

    await db.delete(item)
    await db.commit()

    return {"message": "删除成功"}


# ========== 评分规则管理 ==========
@router.post("", response_model=ScoringRuleResponse)
async def create_rule(
    rule_data: ScoringRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建评分规则"""
    # 检查规则代码是否已存在
    result = await db.execute(
        select(ScoringRule).where(
            ScoringRule.code == rule_data.code,
            ScoringRule.organization_id == rule_data.organization_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="规则代码已存在")

    # 创建规则
    rule = ScoringRule(
        name=rule_data.name,
        code=rule_data.code,
        version=rule_data.version,
        description=rule_data.description,
        organization_id=rule_data.organization_id,
        pass_score=rule_data.pass_score,
        total_score=rule_data.total_score,
        status=RuleStatus.DRAFT,
        is_latest=True,
        created_by=current_user.id,
    )
    db.add(rule)
    await db.flush()

    # 添加规则项
    if rule_data.items:
        for idx, item_data in enumerate(rule_data.items):
            item = RuleItem(
                rule_id=rule.id,
                name=item_data.name,
                code=item_data.code,
                item_type=ItemType(item_data.item_type),
                max_score=item_data.max_score,
                default_score=item_data.default_score,
                is_deduction=item_data.is_deduction,
                deduction_type=item_data.deduction_type,
                deduction_value=item_data.deduction_value,
                is_required=item_data.is_required,
                is_veto=item_data.is_veto,
                tags=item_data.tags,
                category=item_data.category,
                match_prompt=item_data.match_prompt,
                sort_order=item_data.sort_order or idx,
            )
            db.add(item)

    await db.commit()
    await db.refresh(rule)

    return rule


@router.get("", response_model=list[ScoringRuleResponse])
async def list_rules(
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    is_latest: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取规则列表"""
    query = select(ScoringRule).options(selectinload(ScoringRule.items))

    # 权限过滤
    if current_user.organization_id:
        query = query.where(ScoringRule.organization_id == current_user.organization_id)

    if organization_id:
        query = query.where(ScoringRule.organization_id == organization_id)
    if status:
        query = query.where(ScoringRule.status == status)
    if is_latest is not None:
        query = query.where(ScoringRule.is_latest == is_latest)

    query = query.order_by(ScoringRule.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{rule_id}", response_model=ScoringRuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取规则详情"""
    result = await db.execute(
        select(ScoringRule)
        .options(selectinload(ScoringRule.items))
        .where(ScoringRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.put("/{rule_id}", response_model=ScoringRuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: ScoringRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新规则"""
    result = await db.execute(
        select(ScoringRule)
        .options(selectinload(ScoringRule.items))
        .where(ScoringRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule.status != RuleStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的规则才能修改")

    # 更新字段
    update_data = rule_data.model_dump(exclude_unset=True)

    # 处理规则项更新
    if "items" in update_data:
        items_data = update_data.pop("items")
        # 删除旧规则项
        for item in rule.items:
            await db.delete(item)
        # 添加新规则项
        for idx, item_data in enumerate(items_data):
            item = RuleItem(
                rule_id=rule.id,
                name=item_data.name,
                code=item_data.code,
                item_type=ItemType(item_data.item_type),
                max_score=item_data.max_score,
                default_score=item_data.default_score,
                is_deduction=item_data.is_deduction,
                deduction_type=item_data.deduction_type,
                deduction_value=item_data.deduction_value,
                is_required=item_data.is_required,
                is_veto=item_data.is_veto,
                tags=item_data.tags,
                category=item_data.category,
                match_prompt=item_data.match_prompt,
                sort_order=item_data.sort_order or idx,
            )
            db.add(item)

    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return rule


@router.post("/{rule_id}/publish")
async def publish_rule(
    rule_id: int,
    request: RulePublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布规则"""
    result = await db.execute(select(ScoringRule).where(ScoringRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule.status not in [RuleStatus.DRAFT, RuleStatus.TESTING]:
        raise HTTPException(status_code=400, detail="只有草稿或测试状态的规则才能发布")

    # 将旧版本标记为非最新
    await db.execute(
        select(ScoringRule)
        .where(
            ScoringRule.code == rule.code,
            ScoringRule.is_latest == True,
        )
        .update({"is_latest": False})
    )

    # 更新当前规则
    rule.status = RuleStatus.PUBLISHED
    rule.is_latest = True
    rule.published_at = datetime.utcnow()

    await db.commit()

    # 记录审计日志
    await AuditService.log_rule_change(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="publish",
        rule_id=rule_id,
        ip_address="",
    )

    return {"message": "规则发布成功"}


@router.post("/{rule_id}/test")
async def test_rule(
    rule_id: int,
    test_data: RuleTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试规则"""
    # 获取规则
    result = await db.execute(
        select(ScoringRule)
        .options(selectinload(ScoringRule.items))
        .where(ScoringRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 获取测试数据
    if test_data.recording_id:
        # 使用录音测试
        rec_result = await db.execute(
            select(Recording).where(Recording.id == test_data.recording_id)
        )
        recording = rec_result.scalar_one_or_none()
        if not recording:
            raise HTTPException(status_code=404, detail="录音不存在")

        transcript = recording.transcript or ""
        segments = recording.transcript_segments or []
    elif test_data.test_data:
        transcript = test_data.test_data.get("transcript", "")
        segments = test_data.test_data.get("segments", [])
    else:
        raise HTTPException(status_code=400, detail="需要提供测试数据")

    # 执行AI评分
    try:
        scoring_result = await ai_scoring_service.score(
            transcript=transcript,
            segments=segments,
            rule=rule,
        )

        # 保存测试记录
        test_record = RuleTestRecord(
            rule_id=rule_id,
            recording_id=test_data.recording_id,
            total_score=scoring_result["total_score"],
            passed=scoring_result["passed"],
            result_detail=scoring_result,
            tested_by=current_user.id,
            remark=request.remark,
        )
        db.add(test_record)
        await db.commit()

        return {
            "test_record_id": test_record.id,
            "total_score": scoring_result["total_score"],
            "passed": scoring_result["passed"],
            "details": scoring_result["details"],
            "warnings": scoring_result.get("warnings", []),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/{rule_id}/copy")
async def copy_rule(
    rule_id: int,
    new_version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制规则为新版本"""
    result = await db.execute(
        select(ScoringRule)
        .options(selectinload(ScoringRule.items))
        .where(ScoringRule.id == rule_id)
    )
    old_rule = result.scalar_one_or_none()
    if not old_rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 创建新版本
    new_rule = ScoringRule(
        name=old_rule.name,
        code=old_rule.code,
        version=new_version,
        description=old_rule.description,
        organization_id=old_rule.organization_id,
        pass_score=old_rule.pass_score,
        total_score=old_rule.total_score,
        status=RuleStatus.DRAFT,
        is_latest=False,
        parent_id=old_rule.id,
        created_by=current_user.id,
    )
    db.add(new_rule)
    await db.flush()

    # 复制规则项
    for item in old_rule.items:
        new_item = RuleItem(
            rule_id=new_rule.id,
            name=item.name,
            code=item.code,
            item_type=item.item_type,
            max_score=item.max_score,
            default_score=item.default_score,
            is_deduction=item.is_deduction,
            deduction_type=item.deduction_type,
            deduction_value=item.deduction_value,
            is_required=item.is_required,
            is_veto=item.is_veto,
            tags=item.tags,
            category=item.category,
            match_prompt=item.match_prompt,
            sort_order=item.sort_order,
        )
        db.add(new_item)

    await db.commit()
    await db.refresh(new_rule)

    return new_rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除规则"""
    result = await db.execute(select(ScoringRule).where(ScoringRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule.status != RuleStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态的规则才能删除")

    await db.delete(rule)
    await db.commit()

    return {"message": "删除成功"}
