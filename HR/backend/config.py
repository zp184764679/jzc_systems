"""
Configuration module for HR System Backend
Supports multiple environments: development, testing, production
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""

    # Flask - 安全修复：强制环境变量配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import logging
        logger = logging.getLogger(__name__)
        if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
            logger.warning("SECRET_KEY 未设置，使用开发临时密钥")
            SECRET_KEY = "dev-only-temp-key-" + str(os.getpid())
        else:
            raise RuntimeError("SECRET_KEY 环境变量未设置（生产环境必须配置）")

    DEBUG = False
    TESTING = False

    # Database - 安全修复：移除弱默认凭证
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('MYSQL_USER')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'hr_system')

    # 验证数据库凭证
    if not DB_USER or not DB_PASSWORD:
        import logging
        logger = logging.getLogger(__name__)
        if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
            logger.warning("MYSQL_USER/MYSQL_PASSWORD 未设置，使用开发默认值")
            DB_USER = DB_USER or "root"
            DB_PASSWORD = DB_PASSWORD or "root"
        else:
            raise RuntimeError("MYSQL_USER 和 MYSQL_PASSWORD 环境变量必须设置（生产环境）")

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
        'echo': False
    }

    # Server
    PORT = int(os.getenv('PORT', 8003))
    HOST = os.getenv('HOST', '0.0.0.0')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # Log SQL queries
    }


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True

    # Use separate test database
    DB_NAME = os.getenv('TEST_DATABASE', 'cncplan_test')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{DB_NAME}'


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False

    # Require secret key in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production environment")

    # Stricter database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
        'pool_size': 20,
        'max_overflow': 40,
        'echo': False
    }


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
