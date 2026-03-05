"""
用户相关Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ========== 组织 ==========
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 应用组 ==========
class AppGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class AppGroupCreate(AppGroupBase):
    organization_id: int


class AppGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AppGroupResponse(AppGroupBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 用户 ==========
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role: str = "user"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    organization_id: Optional[int] = None
    app_group_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    organization_id: Optional[int] = None
    app_group_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    organization_id: Optional[int]
    app_group_ids: Optional[str]
    is_active: bool
    role: str
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 认证 ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
