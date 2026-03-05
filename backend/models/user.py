"""
用户和组织相关数据模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class UserRole(enum.Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"      # 超级管理员
    ORG_ADMIN = "org_admin"           # 组织管理员
    USER = "user"                     # 普通用户


class Organization(Base):
    """组织（租户）表"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="组织名称")
    code = Column(String(50), unique=True, nullable=False, comment="组织代码")
    description = Column(Text, nullable=True, comment="组织描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    app_groups = relationship("AppGroup", back_populates="organization", cascade="all, delete-orphan")
    rules = relationship("ScoringRule", back_populates="organization", cascade="all, delete-orphan")


class AppGroup(Base):
    """应用组表"""
    __tablename__ = "app_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="应用组名称")
    code = Column(String(50), nullable=False, comment="应用组代码")
    description = Column(Text, nullable=True, comment="应用组描述")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, comment="所属组织ID")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    organization = relationship("Organization", back_populates="app_groups")
    recordings = relationship("Recording", back_populates="app_group", cascade="all, delete-orphan")


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    role = Column(SQLEnum(UserRole), default=UserRole.USER, comment="用户角色")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, comment="所属组织ID")
    app_group_ids = Column(Text, nullable=True, comment="授权应用组ID列表(JSON)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    organization = relationship("Organization", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    scoring_results = relationship("ScoringResult", back_populates="scored_by_user")


class UserPermission(Base):
    """用户权限表"""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    resource = Column(String(50), nullable=False, comment="资源类型")
    action = Column(String(50), nullable=False, comment="操作类型")
    is_allowed = Column(Boolean, default=True, comment="是否允许")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="permissions")


User.permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
