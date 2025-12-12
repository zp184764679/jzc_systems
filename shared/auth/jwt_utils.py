"""
JWT token creation and verification utilities
安全修复: 移除默认密钥，强制要求环境变量配置
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import os
import logging

logger = logging.getLogger(__name__)

# JWT Configuration - 安全修复：强制要求环境变量
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    # 生产环境必须配置 JWT_SECRET_KEY
    logger.warning("JWT_SECRET_KEY 环境变量未设置！使用临时密钥（仅限开发环境）")
    # 仅在开发环境使用临时密钥，生产环境会在部署时配置
    if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
        SECRET_KEY = "dev-only-temp-key-not-for-production-" + str(os.getpid())
    else:
        raise RuntimeError("JWT_SECRET_KEY 环境变量未设置，生产环境必须配置此变量")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary containing user information
            Expected fields: user_id, username, user_type, role, permissions, etc.
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token_from_user(user_dict: Dict[str, Any]) -> str:
    """
    Create JWT token from user dictionary

    Args:
        user_dict: User data from User.to_dict()

    Returns:
        JWT token string
    """
    token_data = {
        "user_id": user_dict["id"],
        "username": user_dict["username"],
        "user_type": user_dict.get("user_type", "employee"),
        "role": user_dict.get("role", "user"),
        "permissions": user_dict.get("permissions", []),
        "emp_no": user_dict.get("emp_no"),
        "supplier_id": user_dict.get("supplier_id"),
        "full_name": user_dict.get("full_name"),
        "is_admin": user_dict.get("is_admin", False),
        "department_id": user_dict.get("department_id"),
        "department_name": user_dict.get("department_name"),
        "position_id": user_dict.get("position_id"),
        "position_name": user_dict.get("position_name"),
        "team_id": user_dict.get("team_id"),
        "team_name": user_dict.get("team_name")
    }

    return create_access_token(token_data)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
