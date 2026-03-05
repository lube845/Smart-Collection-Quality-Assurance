"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "ASR智能质检系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://asr_admin:asr_secure_2024@localhost:5432/asr_quality_db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ASR服务配置
    ASR_API_URL: str = "http://localhost:8001"
    ASR_API_KEY: Optional[str] = None

    # LLM服务配置
    LLM_API_URL: str = "http://localhost:8002"
    LLM_API_KEY: Optional[str] = None

    # 对象存储配置
    OSS_ENDPOINT: str = "http://localhost:9000"
    OSS_ACCESS_KEY: str = "minioadmin"
    OSS_SECRET_KEY: str = "minioadmin"
    OSS_BUCKET: str = "asr-recordings"
    OSS_PUBLIC_BUCKET: str = "asr-public"

    # 音频配置
    AUDIO_MAX_SIZE: int = 500 * 1024 * 1024  # 500MB
    CHUNK_SIZE: int = 5 * 1024 * 1024  # 5MB

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # 预签名URL过期时间(秒)
    PRESIGNED_URL_EXPIRE: int = 300  # 5分钟

    # 审计日志配置
    AUDIT_LOG_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
