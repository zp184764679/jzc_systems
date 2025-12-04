"""
Authentication API endpoints for quotation system
"""
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Header
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.auth import (
    User,
    init_auth_db,
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    has_system_permission,
    is_admin,
    Roles
)
from shared.auth.models import get_auth_db

router = APIRouter()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    emp_no: Optional[str]
    role: Optional[str]
    permissions: Optional[list]
    is_active: bool
    is_admin: bool


class SSOLoginRequest(BaseModel):
    """SSO login request model"""
    token: str


@router.post("/sso-login")
async def sso_login(request: SSOLoginRequest):
    """
    SSO login endpoint - accepts token from Portal

    Validates the token and returns user info
    """
    if not request.token:
        raise HTTPException(status_code=400, detail="缺少token")

    # Verify token
    payload = verify_token(request.token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    return {
        'message': 'SSO登录成功',
        'user': payload
    }


@router.post("/login")
async def login(login_data: LoginRequest, response: Response, db=Depends(get_auth_db)):
    """
    User login endpoint

    Returns JWT token in httpOnly cookie
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    # Check if user has quotation system permission (admins have access to all systems)
    if not has_system_permission(user.permissions, 'quotation') and not is_admin(user.role):
        raise HTTPException(status_code=403, detail="您没有访问报价系统的权限，请联系管理员")

    # Create JWT token with comprehensive user data
    token_data = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'emp_no': user.emp_no,
        'role': user.role,
        'is_admin': user.is_admin,  # Backward compatibility
    }
    access_token = create_access_token(token_data)

    # Set httpOnly cookie
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite='lax',
        path='/',
        max_age=28800  # 8 hours
    )

    return {
        'message': '登录成功',
        'user': user.to_dict(),
        'token': access_token  # Also send token in response body for clients that prefer it
    }


@router.post("/logout")
async def logout(response: Response):
    """
    User logout endpoint

    Clears the JWT cookie
    """
    response.delete_cookie(key='access_token', path='/')
    return {'message': '退出登录成功'}


@router.get("/me")
async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_auth_db)
):
    """
    Get current authenticated user

    Reads JWT from cookie or Authorization header
    """
    # Try cookie first
    token = access_token
    
    # Fall back to Authorization header
    if not token and authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    # Get user from database
    user_id = payload.get('user_id')
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    return user.to_dict()


# Dependency for protected routes
async def get_current_active_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_auth_db)
) -> User:
    """
    Dependency to get current authenticated user for protected routes
    """
    # Try cookie first
    token = access_token
    
    # Fall back to Authorization header
    if not token and authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    # Get user from database
    user_id = payload.get('user_id')
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    return user


# Dependency for admin-only routes
async def get_current_admin_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_auth_db)
) -> User:
    """
    Dependency to get current admin user for admin-only routes
    """
    # Try cookie first
    token = access_token
    
    # Fall back to Authorization header
    if not token and authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    # Get user from database
    user_id = payload.get('user_id')
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # Check admin permission
    if not is_admin(user.role):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    return user
