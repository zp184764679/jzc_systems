# config/settings.py
"""
系统配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "机加工报价系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    # MySQL: mysql+pymysql://username:password@localhost:3306/database_name
    # SQLite: sqlite:///./quote_system.db
    DATABASE_URL: str = "mysql+pymysql://app:app@localhost/quotation?charset=utf8mb4"

    # JWT认证
    SECRET_KEY: str = os.getenv('JWT_SECRET', 'change-this-secret-in-production-immediately')
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


# 创建全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "drawings"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "quotes"), exist_ok=True)
