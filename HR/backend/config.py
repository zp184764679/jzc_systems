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

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('MYSQL_USER', 'root')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'cncplan')

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
