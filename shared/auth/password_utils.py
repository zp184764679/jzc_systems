"""
Password hashing and verification utilities
"""
import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Convert password to bytes and hash it
    # bcrypt automatically truncates passwords longer than 72 bytes
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash
    P2-19: 改进异常处理，添加日志记录
    """
    if not plain_password or not hashed_password:
        logger.warning('[verify_password] Empty password or hash provided')
        return False

    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError as e:
        # P2-19: 无效的哈希格式（如非 bcrypt 哈希）
        logger.error(f'[verify_password] Invalid hash format: {e}')
        return False
    except Exception as e:
        # P2-19: 其他未知异常
        logger.error(f'[verify_password] Unexpected error: {type(e).__name__}: {e}')
        return False
