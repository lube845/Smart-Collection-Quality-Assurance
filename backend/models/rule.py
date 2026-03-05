"""
评分规则相关数据模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum,
    JSON, Float
)
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class RuleStatus(enum.Enum):
    """规则状态枚举"""
    DRAFT = "draft"             # 草稿
    TESTING = "testing"         # 测试中
    PUBLISHED = "published"    # 已发布
    DEPRECATED = "deprecated"   # 已废弃


class ItemType(enum.Enum):
    """考核项类型枚举"""
    ASSESSMENT = "assessment"   # 考核项
    CONFIRM = "confirm"         # 信息确认项


class ScoringRule(Base):
    """评分规则表"""
    __tablename__ = "scoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    code = Column(String(50), nullable=False, comment="规则代码")
    version = Column(String(20), nullable=False, comment="规则版本号")
    description = Column(Text, nullable=True, comment="规则描述")

    # 所属组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, comment="所属组织ID")

    # 规则配置
    pass_score = Column(Float, default=60.0, comment="及格分数")
    total_score = Column(Float, default=100.0, comment="总分")

    # 状态
    status = Column(SQLEnum(RuleStatus), default=RuleStatus.DRAFT, comment="状态")
    is_latest = Column(Boolean, default=True, comment="是否为最新版本")

    # 上一版本
    parent_id = Column(Integer, ForeignKey("scoring_rules.id"), nullable=True, comment="上一版本ID")

    remark = Column(Text, nullable=True, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    published_at = Column(DateTime, nullable=True, comment="发布时间")

    # 关系
    organization = relationship("Organization", back_populates="rules")
    creator = relationship("User")
    items = relationship("RuleItem", back_populates="rule", cascade="all, delete-orphan")
    scoring_results = relationship("ScoringResult", back_populates="rule")

    # 自引用关系
    parent = relationship("ScoringRule", remote_side=[id], backref="children")


class RuleItem(Base):
    """规则考核项表"""
    __tablename__ = "rule_items"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("scoring_rules.id"), nullable=False, comment="所属规则ID")
    name = Column(String(200), nullable=False, comment="考核项名称")
    code = Column(String(50), nullable=False, comment="考核项代码")
    item_type = Column(SQLEnum(ItemType), nullable=False, comment="考核项类型")

    # 评分配置
    max_score = Column(Float, nullable=False, comment="满分")
    default_score = Column(Float, default=0.0, comment="默认得分")

    # 加分/扣分配置
    is_deduction = Column(Boolean, default=True, comment="是否为扣分项")
    deduction_type = Column(String(20), nullable=True, comment="扣分方式(fixed/percentage)")
    deduction_value = Column(Float, nullable=True, comment="扣分值")

    # 是否为必检项
    is_required = Column(Boolean, default=True, comment="是否必检")

    # 是否为一票否决项
    is_veto = Column(Boolean, default=False, comment="是否一票否决项")

    # 标签分类
    tags = Column(JSON, nullable=True, comment="标签(JSON数组)")
    category = Column(String(50), nullable=True, comment="分类")

    # 匹配规则（供AI使用）
    match_prompt = Column(Text, nullable=True, comment="匹配提示词")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序")

    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    rule = relationship("ScoringRule", back_populates="items")


class RuleTestRecord(Base):
    """规则测试记录表"""
    __tablename__ = "rule_test_records"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("scoring_rules.id"), nullable=False, comment="规则ID")
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=True, comment="测试录音ID")

    # 测试结果
    total_score = Column(Float, nullable=False, comment="测试得分")
    passed = Column(Boolean, nullable=False, comment="是否通过")
    result_detail = Column(JSON, nullable=True, comment="详细结果(JSON)")

    # 测试人
    tested_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="测试人ID")

    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    rule = relationship("ScoringRule")
    recording = relationship("Recording")
    tester = relationship("User")
