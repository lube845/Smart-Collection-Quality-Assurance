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

    # ==================== 数据库配置 ====================
    # 是否运行在Docker环境中
    IS_DOCKER: bool = False

    # MySQL数据库配置（Docker内）
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "asr_admin"
    DB_PASSWORD: str = "asr_secure_2024"
    DB_NAME: str = "asr_quality_db"

    # MySQL数据库配置（外部服务器）
    DB_EXTERNAL_HOST: str = "localhost"
    DB_EXTERNAL_PORT: int = 3306
    DB_EXTERNAL_USER: str = "root"
    DB_EXTERNAL_PASSWORD: str = ""
    DB_EXTERNAL_NAME: str = "asr_quality_db"

    # 数据库连接URL（动态生成）
    @property
    def DATABASE_URL(self) -> str:
        """根据IS_DOCKER配置动态生成数据库连接URL"""
        if self.IS_DOCKER:
            # Docker内连接
            return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            # 外部服务器连接
            return f"mysql+aiomysql://{self.DB_EXTERNAL_USER}:{self.DB_EXTERNAL_PASSWORD}@{self.DB_EXTERNAL_HOST}:{self.DB_EXTERNAL_PORT}/{self.DB_EXTERNAL_NAME}"

    # 同步数据库连接URL（用于Alembic迁移）
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """同步数据库连接URL"""
        if self.IS_DOCKER:
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"mysql+pymysql://{self.DB_EXTERNAL_USER}:{self.DB_EXTERNAL_PASSWORD}@{self.DB_EXTERNAL_HOST}:{self.DB_EXTERNAL_PORT}/{self.DB_EXTERNAL_NAME}"

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
