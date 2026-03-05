"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..core.database import get_db
from ..models.user import User, Organization
from ..schemas.user import (
    UserCreate, UserResponse, UserUpdate,
    OrganizationCreate, OrganizationResponse, OrganizationUpdate,
    LoginRequest, TokenResponse, RefreshTokenRequest,
)
from ..services.auth_service import (
    AuthService, get_current_user, get_password_hash
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    result = await AuthService.login(db, request.username, request.password)

    # 排除用户敏感信息
    user_data = {
        "id": result["user"].id,
        "username": result["user"].username,
        "email": result["user"].email,
        "role": result["user"].role.value,
    }

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    result = await AuthService.refresh_token(request.refresh_token, db)
    return TokenResponse(**result)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 在实际应用中，应该将令牌加入黑名单
    return {"message": "登出成功"}


# ========== 用户管理 ==========
user_router = APIRouter(prefix="/users", tags=["用户管理"])


@user_router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已被使用")

    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        organization_id=user_data.organization_id,
        app_group_ids=str(user_data.app_group_ids) if user_data.app_group_ids else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@user_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)
    if "app_group_ids" in update_data:
        update_data["app_group_ids"] = str(update_data["app_group_ids"])

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


# ========== 组织管理 ==========
org_router = APIRouter(prefix="/organizations", tags=["组织管理"])


@org_router.post("", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建组织"""
    # 检查组织代码是否已存在
    result = await db.execute(select(Organization).where(Organization.code == org_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="组织代码已存在")

    organization = Organization(
        name=org_data.name,
        code=org_data.code,
        description=org_data.description,
    )
    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


@org_router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织列表"""
    result = await db.execute(select(Organization).where(Organization.is_active == True))
    return result.scalars().all()


@org_router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织详情"""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    return org


@org_router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新组织"""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org
