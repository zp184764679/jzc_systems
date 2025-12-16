# config/settings.py
"""
系统配置文件
安全修复：移除硬编码凭证，强制环境变量配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# 在类定义前加载 .env 文件
load_dotenv()


def _get_database_url() -> str:
    """安全构建数据库连接字符串"""
    url = os.getenv('DATABASE_URL')
    if url:
        return url
    # 从各环境变量构建
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    db = os.getenv('MYSQL_DATABASE', 'quotation')
    if user and password:
        return f"mysql+pymysql://{user}:{password}@{host}/{db}?charset=utf8mb4"
    # 开发环境回退
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG', '').lower() == 'true':
        import logging
        logging.warning("数据库凭证未设置，使用开发默认值")
        return "mysql+pymysql://root:root@localhost/quotation?charset=utf8mb4"
    raise RuntimeError("DATABASE_URL 或 MYSQL_USER/MYSQL_PASSWORD 环境变量必须设置")


def _get_secret_key() -> str:
    """安全获取 JWT 密钥"""
    key = os.getenv('JWT_SECRET') or os.getenv('SECRET_KEY')
    if key:
        return key
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG', '').lower() == 'true':
        import logging
        logging.warning("JWT_SECRET 未设置，使用开发临时密钥")
        return f"dev-only-temp-key-{os.getpid()}"
    raise RuntimeError("JWT_SECRET 环境变量必须设置（生产环境）")


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "机加工报价系统"
    APP_VERSION: str = "1.0.0"
    # 安全修复：默认关闭 debug 模式
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # 数据库配置 - 安全修复：不再硬编码凭证
    DATABASE_URL: str = _get_database_url()

    # JWT认证 - 安全修复：强制环境变量
    SECRET_KEY: str = _get_secret_key()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Ollama Vision配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_VISION_MODEL: str = "qwen3-vl:8b-instruct"

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50  # MB
    ALLOWED_EXTENSIONS: list = ["pdf", "png", "jpg", "jpeg"]

    # Redis配置
    REDIS_URL: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 跨系统API配置
    CRM_API_BASE_URL: str = "http://localhost:8002"
    HR_API_BASE_URL: str = "http://localhost:8003"
    PDM_API_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略 .env 中的额外字段（如 AUTH_DB_* 供 shared/auth 使用）


# 创建全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "drawings"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "quotes"), exist_ok=True)
