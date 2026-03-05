"""
Schema定义
"""
from .user import (
    OrganizationBase, OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    AppGroupBase, AppGroupCreate, AppGroupUpdate, AppGroupResponse,
    UserBase, UserCreate, UserUpdate, UserResponse,
    LoginRequest, TokenResponse, RefreshTokenRequest,
)
from .recording import (
    RecordingBase, RecordingUploadInit, RecordingResponse, RecordingDetailResponse,
    RecordingQuery, RecordingListResponse,
    TranscriptSegmentResponse, TranscriptResponse,
    ScoringDetailResponse, ScoringResultResponse, RecordingScoreResponse,
)
from .rule import (
    RuleItemBase, RuleItemCreate, RuleItemUpdate, RuleItemResponse,
    ScoringRuleBase, ScoringRuleCreate, ScoringRuleUpdate, ScoringRuleResponse,
    RuleTestCreate, RuleTestResponse, RulePublishRequest,
)

__all__ = [
    # 用户相关
    "OrganizationBase", "OrganizationCreate", "OrganizationUpdate", "OrganizationResponse",
    "AppGroupBase", "AppGroupCreate", "AppGroupUpdate", "AppGroupResponse",
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "LoginRequest", "TokenResponse", "RefreshTokenRequest",
    # 录音相关
    "RecordingBase", "RecordingUploadInit", "RecordingResponse", "RecordingDetailResponse",
    "RecordingQuery", "RecordingListResponse",
    "TranscriptSegmentResponse", "TranscriptResponse",
    "ScoringDetailResponse", "ScoringResultResponse", "RecordingScoreResponse",
    # 规则相关
    "RuleItemBase", "RuleItemCreate", "RuleItemUpdate", "RuleItemResponse",
    "ScoringRuleBase", "ScoringRuleCreate", "ScoringRuleUpdate", "ScoringRuleResponse",
    "RuleTestCreate", "RuleTestResponse", "RulePublishRequest",
]
