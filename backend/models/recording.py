"""
录音和转写相关数据模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum,
    JSON, Float
)
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class RecordingStatus(enum.Enum):
    """录音状态枚举"""
    UPLOADING = "uploading"           # 上传中
    UPLOADED = "uploaded"             # 已上传
    TRANSCRIBING = "transcribing"     # 转写中
    TRANSCRIBED = "transcribed"       # 已转写
    TRANSCRIBE_FAILED = "transcribe_failed"  # 转写失败
    SCORING = "scoring"               # 评分中
    SCORED = "scored"                 # 已评分
    SCORE_FAILED = "score_failed"     # 评分失败


class RiskLevel(enum.Enum):
    """风险等级枚举"""
    NORMAL = "normal"         # 正常
    WARNING = "warning"       # 警告
    DANGER = "danger"        # 危险（一票否决）


class Recording(Base):
    """录音文件表"""
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False, comment="文件名称")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    file_md5 = Column(String(32), nullable=False, index=True, comment="文件MD5")
    file_type = Column(String(20), nullable=False, comment="文件类型(mp3/wav/amr)")
    duration = Column(Float, nullable=True, comment="音频时长(秒)")

    # 对象存储信息
    oss_object_key = Column(String(500), nullable=False, comment="OSS对象键")
    oss_bucket = Column(String(100), nullable=False, comment="OSS存储桶")

    # 业务信息
    app_group_id = Column(Integer, ForeignKey("app_groups.id"), nullable=False, comment="应用组ID")
    agent_id = Column(String(50), nullable=True, comment="坐席工号")
    agent_name = Column(String(100), nullable=True, comment="坐席姓名")
    customer_id = Column(String(50), nullable=True, comment="客户ID")
    customer_phone = Column(String(20), nullable=True, comment="客户手机号")
    call_id = Column(String(100), nullable=True, comment="通话记录ID")
    call_time = Column(DateTime, nullable=True, comment="通话时间")

    # 状态
    status = Column(SQLEnum(RecordingStatus), default=RecordingStatus.UPLOADING, comment="状态")
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.NORMAL, comment="风险等级")

    # 转写信息
    transcript = Column(Text, nullable=True, comment="转写文本(JSON)")
    transcript_segments = Column(JSON, nullable=True, comment="转写片段(带时间戳)")

    # 评分信息
    total_score = Column(Float, nullable=True, comment="总分")
    rule_version = Column(String(20), nullable=True, comment="评分规则版本")

    # 备注
    remark = Column(Text, nullable=True, comment="备注")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="上传人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    app_group = relationship("AppGroup", back_populates="recordings")
    creator = relationship("User", foreign_keys=[created_by])
    scoring_results = relationship("ScoringResult", back_populates="recording", cascade="all, delete-orphan")
    scoring_details = relationship("ScoringDetail", back_populates="recording", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    """转写片段表（带时间戳的对话）"""
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False, comment="录音ID")
    speaker = Column(String(20), nullable=False, comment="说话人(agent/customer)")
    speaker_name = Column(String(100), nullable=True, comment="说话人名称")
    start_time = Column(Float, nullable=False, comment="开始时间(秒)")
    end_time = Column(Float, nullable=False, comment="结束时间(秒)")
    text = Column(Text, nullable=False, comment="转写文本")
    confidence = Column(Float, nullable=True, comment="置信度")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    recording = relationship("Recording")


class ScoringResult(Base):
    """评分结果表"""
    __tablename__ = "scoring_results"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False, comment="录音ID")
    rule_id = Column(Integer, ForeignKey("scoring_rules.id"), nullable=False, comment="规则ID")
    total_score = Column(Float, nullable=False, comment="总分")
    passed = Column(Boolean, nullable=False, comment="是否通过")
    is_rejected = Column(Boolean, default=False, comment="是否一票否决")

    # 评分人
    scored_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="评分人ID")
    scored_at = Column(DateTime, nullable=True, comment="评分时间")

    # AI评分标识
    is_auto_scored = Column(Boolean, default=True, comment="是否自动评分")
    ai_model = Column(String(100), nullable=True, comment="AI模型名称")

    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    recording = relationship("Recording", back_populates="scoring_results")
    rule = relationship("ScoringRule")
    scored_by_user = relationship("User", back_populates="scoring_results")
    details = relationship("ScoringDetail", back_populates="scoring_result", cascade="all, delete-orphan")


class ScoringDetail(Base):
    """评分明细表"""
    __tablename__ = "scoring_details"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False, comment="录音ID")
    scoring_result_id = Column(Integer, ForeignKey("scoring_results.id"), nullable=False, comment="评分结果ID")

    # 考核项信息
    rule_item_id = Column(Integer, ForeignKey("rule_items.id"), nullable=False, comment="考核项ID")
    item_name = Column(String(200), nullable=False, comment="考核项名称")
    item_type = Column(String(20), nullable=False, comment="考核项类型(assessment/confirm)")

    # 评分
    status = Column(String(20), nullable=False, comment="状态(done/not_done/wrong)")
    score = Column(Float, nullable=False, comment="得分")
    max_score = Column(Float, nullable=False, comment="该项满分")

    # 匹配信息
    matched_text = Column(Text, nullable=True, comment="匹配文本")
    matched_segment_ids = Column(JSON, nullable=True, comment="匹配的片段ID")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    recording = relationship("Recording", back_populates="scoring_details")
    scoring_result = relationship("ScoringResult", back_populates="details")
    rule_item = relationship("RuleItem")
