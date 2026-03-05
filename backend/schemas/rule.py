"""
规则相关Schema
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========== 规则项 ==========
class RuleItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    item_type: str = "assessment"
    max_score: float = Field(..., gt=0)
    default_score: float = 0.0
    is_deduction: bool = True
    deduction_type: Optional[str] = None
    deduction_value: Optional[float] = None
    is_required: bool = True
    is_veto: bool = False
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    match_prompt: Optional[str] = None
    sort_order: int = 0


class RuleItemCreate(RuleItemBase):
    pass


class RuleItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    item_type: Optional[str] = None
    max_score: Optional[float] = Field(None, gt=0)
    default_score: Optional[float] = None
    is_deduction: Optional[bool] = None
    deduction_type: Optional[str] = None
    deduction_value: Optional[float] = None
    is_required: Optional[bool] = None
    is_veto: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    match_prompt: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RuleItemResponse(RuleItemBase):
    id: int
    rule_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 评分规则 ==========
class ScoringRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    version: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    pass_score: float = 60.0
    total_score: float = 100.0


class ScoringRuleCreate(ScoringRuleBase):
    organization_id: int
    items: Optional[List[RuleItemCreate]] = None


class ScoringRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    pass_score: Optional[float] = Field(None, gt=0)
    total_score: Optional[float] = Field(None, gt=0)
    items: Optional[List[RuleItemCreate]] = None


class ScoringRuleResponse(ScoringRuleBase):
    id: int
    organization_id: int
    status: str
    is_latest: bool
    parent_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    items: List[RuleItemResponse] = []

    class Config:
        from_attributes = True


# ========== 规则测试 ==========
class RuleTestCreate(BaseModel):
    rule_id: int
    recording_id: Optional[int] = None
    test_data: Optional[dict] = None


class RuleTestResponse(BaseModel):
    id: int
    rule_id: int
    recording_id: Optional[int]
    total_score: float
    passed: bool
    result_detail: Optional[dict]
    tested_by: int
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 规则发布 ==========
class RulePublishRequest(BaseModel):
    rule_id: int
    remark: Optional[str] = None
