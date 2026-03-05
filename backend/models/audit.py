"""
审计日志相关数据模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 操作人
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作人ID")
    username = Column(String(50), nullable=True, comment="操作人用户名")
    ip_address = Column(String(50), nullable=True, comment="IP地址")

    # 操作信息
    action = Column(String(50), nullable=False, comment="操作类型")
    resource = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(String(100), nullable=True, comment="资源ID")
    method = Column(String(10), nullable=True, comment="请求方法")

    # 请求信息
    request_url = Column(String(500), nullable=True, comment="请求URL")
    request_body = Column(JSON, nullable=True, comment="请求体")
    request_params = Column(JSON, nullable=True, comment="请求参数")

    # 响应信息
    response_status = Column(Integer, nullable=True, comment="响应状态码")
    response_message = Column(Text, nullable=True, comment="响应消息")

    # 额外信息
    extra = Column(JSON, nullable=True, comment="额外信息")

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="audit_logs")


class DataRetention(Base):
    """数据保留策略表"""
    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="策略名称")
    resource = Column(String(50), nullable=False, comment="资源类型")

    # 保留期限（天）
    retention_days = Column(Integer, nullable=False, comment="保留天数")

    # 过期操作
    action_on_expiry = Column(String(20), nullable=False, comment="过期操作(archive/delete)")
    archive_bucket = Column(String(100), nullable=True, comment="归档存储桶")

    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
