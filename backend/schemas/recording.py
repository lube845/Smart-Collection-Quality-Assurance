"""
录音相关Schema
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========== 录音文件 ==========
class RecordingBase(BaseModel):
    file_name: str
    file_size: int
    file_md5: str
    file_type: str
    app_group_id: int
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    customer_id: Optional[str] = None
    customer_phone: Optional[str] = None
    call_id: Optional[str] = None
    call_time: Optional[datetime] = None


class RecordingUploadInit(BaseModel):
    """初始化上传"""
    file_name: str
    file_size: int
    file_md5: str
    file_type: str
    app_group_id: int
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    customer_id: Optional[str] = None
    customer_phone: Optional[str] = None
    call_id: Optional[str] = None
    call_time: Optional[datetime] = None


class RecordingUploadPart(BaseModel):
    """分片上传"""
    upload_id: str
    part_number: int
    content: bytes


class RecordingResponse(BaseModel):
    id: int
    file_name: str
    file_size: int
    file_type: str
    duration: Optional[float]
    status: str
    risk_level: str
    total_score: Optional[float]
    agent_id: Optional[str]
    agent_name: Optional[str]
    customer_phone: Optional[str]
    call_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecordingDetailResponse(RecordingResponse):
    transcript: Optional[str] = None
    transcript_segments: Optional[List[dict]] = None

    class Config:
        from_attributes = True


# ========== 转写 ==========
class TranscriptSegmentResponse(BaseModel):
    id: int
    speaker: str
    speaker_name: Optional[str]
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float]

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    recording_id: int
    full_text: str
    segments: List[TranscriptSegmentResponse]


# ========== 评分 ==========
class ScoringDetailResponse(BaseModel):
    id: int
    item_name: str
    item_type: str
    status: str
    score: float
    max_score: float
    matched_text: Optional[str]

    class Config:
        from_attributes = True


class ScoringResultResponse(BaseModel):
    id: int
    total_score: float
    passed: bool
    is_rejected: bool
    is_auto_scored: bool
    ai_model: Optional[str]
    scored_by: Optional[int]
    scored_at: Optional[datetime]
    remark: Optional[str]
    details: List[ScoringDetailResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class RecordingScoreResponse(BaseModel):
    recording: RecordingDetailResponse
    scoring_result: ScoringResultResponse


# ========== 查询参数 ==========
class RecordingQuery(BaseModel):
    """录音查询参数"""
    app_group_id: Optional[int] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    agent_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20


class RecordingListResponse(BaseModel):
    """录音列表响应"""
    items: List[RecordingResponse]
    total: int
    page: int
    page_size: int
