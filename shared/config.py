# shared/config.py
"""
P3-42: 统一配置管理模块

提供跨系统的配置管理功能：
- 统一环境变量加载
- 配置验证
- 多环境支持
- 类型安全配置访问
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env_file(env_file: str = None):
    """加载环境变量文件"""
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
        logger.info(f"已加载环境变量文件: {env_file}")
    else:
        # 尝试加载默认的 .env 文件
        load_dotenv()


def get_env(key: str, default: str = None, required: bool = False) -> Optional[str]:
    """
    获取环境变量

    Args:
        key: 环境变量名
        default: 默认值
        required: 是否必须

    Returns:
        环境变量值或默认值

    Raises:
        ValueError: 如果 required=True 但环境变量未设置
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"必需的环境变量未设置: {key}")
    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型环境变量"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数类型环境变量"""
    value = os.getenv(key, str(default))
    try:
        return int(value)
    except ValueError:
        logger.warning(f"环境变量 {key} 值 '{value}' 无法转换为整数，使用默认值 {default}")
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """获取浮点数类型环境变量"""
    value = os.getenv(key, str(default))
    try:
        return float(value)
    except ValueError:
        logger.warning(f"环境变量 {key} 值 '{value}' 无法转换为浮点数，使用默认值 {default}")
        return default


def get_env_list(key: str, default: List[str] = None, separator: str = ',') -> List[str]:
    """获取列表类型环境变量"""
    value = os.getenv(key)
    if not value:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = 'localhost'
    port: int = 3306
    user: str = ''
    password: str = ''
    database: str = ''
    uri: str = ''

    @classmethod
    def from_env(cls, prefix: str = '', db_name: str = 'cncplan') -> 'DatabaseConfig':
        """从环境变量创建数据库配置"""
        # 优先使用完整 URI
        uri = os.getenv(f'{prefix}DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
        if uri:
            return cls(uri=uri)

        # 否则使用分开的配置
        host = os.getenv(f'{prefix}DB_HOST', 'localhost')
        port = get_env_int(f'{prefix}DB_PORT', 3306)
        user = os.getenv(f'{prefix}MYSQL_USER') or os.getenv('MYSQL_USER', '')
        password = os.getenv(f'{prefix}MYSQL_PASSWORD') or os.getenv('MYSQL_PASSWORD', '')
        database = os.getenv(f'{prefix}MYSQL_DATABASE') or os.getenv('MYSQL_DATABASE', db_name)

        # 开发环境使用默认值
        if not user or not password:
            flask_env = os.getenv('FLASK_ENV', 'development')
            flask_debug = get_env_bool('FLASK_DEBUG', False)
            if flask_env == 'development' or flask_debug:
                user = user or 'app'
                password = password or 'app'
                logger.debug(f"开发环境使用默认数据库凭据")

        return cls(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            uri=f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}" if user else ''
        )

    def get_uri(self) -> str:
        """获取数据库连接 URI"""
        if self.uri:
            return self.uri
        if not self.user:
            raise ValueError("数据库用户名未配置")
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class JWTConfig:
    """JWT 认证配置"""
    secret_key: str = ''
    algorithm: str = 'HS256'
    expiration_hours: int = 8

    # 开发环境默认密钥
    DEV_SECRET_KEY = 'jzc-dev-shared-secret-key-2025'

    @classmethod
    def from_env(cls) -> 'JWTConfig':
        """从环境变量创建 JWT 配置"""
        secret_key = os.getenv('JWT_SECRET_KEY') or os.getenv('SECRET_KEY')

        # 开发环境使用默认密钥
        if not secret_key:
            flask_env = os.getenv('FLASK_ENV', 'development')
            flask_debug = get_env_bool('FLASK_DEBUG', False)
            if flask_env == 'development' or flask_debug:
                secret_key = cls.DEV_SECRET_KEY
                logger.debug("开发环境使用默认 JWT 密钥")
            else:
                logger.warning("生产环境必须设置 JWT_SECRET_KEY")

        return cls(
            secret_key=secret_key or '',
            algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
            expiration_hours=get_env_int('JWT_EXPIRATION_HOURS', 8)
        )

    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.secret_key:
            return False
        if self.secret_key == self.DEV_SECRET_KEY:
            flask_env = os.getenv('FLASK_ENV', 'development')
            if flask_env == 'production':
                logger.error("生产环境不能使用默认 JWT 密钥!")
                return False
        return True


@dataclass
class CORSConfig:
    """CORS 跨域配置"""
    origins: List[str] = field(default_factory=list)
    allow_credentials: bool = True
    max_age: int = 3600

    @classmethod
    def from_env(cls) -> 'CORSConfig':
        """从环境变量创建 CORS 配置"""
        origins_str = os.getenv('CORS_ORIGINS') or os.getenv('ALLOWED_ORIGINS', '')
        origins = [o.strip() for o in origins_str.split(',') if o.strip()]

        return cls(
            origins=origins,
            allow_credentials=get_env_bool('CORS_ALLOW_CREDENTIALS', True),
            max_age=get_env_int('CORS_MAX_AGE', 3600)
        )


@dataclass
class RedisConfig:
    """Redis 缓存配置"""
    url: str = 'redis://localhost:6379/0'
    prefix: str = 'app'
    default_ttl: int = 3600

    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """从环境变量创建 Redis 配置"""
        return cls(
            url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            prefix=os.getenv('CACHE_PREFIX', 'app'),
            default_ttl=get_env_int('CACHE_DEFAULT_TTL', 3600)
        )


@dataclass
class CeleryConfig:
    """Celery 异步任务配置"""
    broker_url: str = 'redis://localhost:6379/0'
    result_backend: str = 'redis://localhost:6379/1'
    task_default_queue: str = 'default'
    worker_concurrency: int = 2
    task_time_limit: int = 180
    task_soft_time_limit: int = 120

    @classmethod
    def from_env(cls) -> 'CeleryConfig':
        """从环境变量创建 Celery 配置"""
        return cls(
            broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
            task_default_queue=os.getenv('CELERY_TASK_DEFAULT_QUEUE', 'default'),
            worker_concurrency=get_env_int('CELERY_WORKER_CONCURRENCY', 2),
            task_time_limit=get_env_int('CELERY_TASK_TIME_LIMIT', 180),
            task_soft_time_limit=get_env_int('CELERY_TASK_SOFT_TIME_LIMIT', 120)
        )


@dataclass
class ServiceURLConfig:
    """系统集成 API URL 配置"""
    portal_url: str = 'http://localhost:3002'
    hr_url: str = 'http://localhost:8003'
    account_url: str = 'http://localhost:8004'
    quotation_url: str = 'http://localhost:8001'
    caigou_url: str = 'http://localhost:5001'
    shm_url: str = 'http://localhost:8006'
    crm_url: str = 'http://localhost:8002'
    scm_url: str = 'http://localhost:8005'
    eam_url: str = 'http://localhost:8008'
    mes_url: str = 'http://localhost:8007'
    pdm_url: str = 'http://localhost:8001'
    dashboard_url: str = 'http://localhost:8100'

    @classmethod
    def from_env(cls) -> 'ServiceURLConfig':
        """从环境变量创建服务 URL 配置"""
        return cls(
            portal_url=os.getenv('PORTAL_API_BASE_URL', 'http://localhost:3002'),
            hr_url=os.getenv('HR_API_BASE_URL', 'http://localhost:8003'),
            account_url=os.getenv('ACCOUNT_API_BASE_URL', 'http://localhost:8004'),
            quotation_url=os.getenv('QUOTATION_API_BASE_URL', 'http://localhost:8001'),
            caigou_url=os.getenv('CAIGOU_API_BASE_URL', 'http://localhost:5001'),
            shm_url=os.getenv('SHM_API_BASE_URL', 'http://localhost:8006'),
            crm_url=os.getenv('CRM_API_BASE_URL', 'http://localhost:8002'),
            scm_url=os.getenv('SCM_API_BASE_URL', 'http://localhost:8005'),
            eam_url=os.getenv('EAM_API_BASE_URL', 'http://localhost:8008'),
            mes_url=os.getenv('MES_API_BASE_URL', 'http://localhost:8007'),
            pdm_url=os.getenv('PDM_API_BASE_URL', 'http://localhost:8001'),
            dashboard_url=os.getenv('DASHBOARD_API_BASE_URL', 'http://localhost:8100')
        )


@dataclass
class AppConfig:
    """应用全局配置"""
    name: str = ''
    env: str = 'development'
    debug: bool = False
    port: int = 5000
    host: str = '0.0.0.0'

    # 子配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    jwt: JWTConfig = field(default_factory=JWTConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    services: ServiceURLConfig = field(default_factory=ServiceURLConfig)

    @classmethod
    def from_env(cls, app_name: str = '', default_port: int = 5000, db_name: str = 'cncplan') -> 'AppConfig':
        """
        从环境变量创建应用配置

        Args:
            app_name: 应用名称
            default_port: 默认端口
            db_name: 默认数据库名称
        """
        return cls(
            name=app_name,
            env=os.getenv('FLASK_ENV', 'development'),
            debug=get_env_bool('FLASK_DEBUG', False),
            port=get_env_int('PORT', default_port),
            host=os.getenv('HOST', '0.0.0.0'),
            database=DatabaseConfig.from_env(db_name=db_name),
            jwt=JWTConfig.from_env(),
            cors=CORSConfig.from_env(),
            redis=RedisConfig.from_env(),
            services=ServiceURLConfig.from_env()
        )

    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.env == 'production'

    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return self.env == 'development' or self.debug

    def validate(self) -> Dict[str, Any]:
        """
        验证配置是否有效

        Returns:
            dict: {'valid': bool, 'errors': list, 'warnings': list}
        """
        errors = []
        warnings = []

        # 验证 JWT
        if not self.jwt.validate():
            if self.is_production():
                errors.append("生产环境必须设置 JWT_SECRET_KEY")
            else:
                warnings.append("使用默认 JWT 密钥，仅限开发环境")

        # 验证数据库
        if not self.database.user and not self.database.uri:
            if self.is_production():
                errors.append("生产环境必须配置数据库凭据")
            else:
                warnings.append("使用默认数据库凭据，仅限开发环境")

        # 验证 CORS
        if not self.cors.origins and self.is_production():
            warnings.append("生产环境建议配置 CORS_ORIGINS")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def print_config_summary(config: AppConfig):
    """打印配置摘要（用于调试）"""
    validation = config.validate()

    print(f"\n{'='*50}")
    print(f"应用配置摘要: {config.name or 'Unnamed App'}")
    print(f"{'='*50}")
    print(f"环境: {config.env}")
    print(f"调试模式: {config.debug}")
    print(f"端口: {config.port}")
    print(f"数据库: {config.database.database}@{config.database.host}")
    print(f"JWT 密钥: {'已配置' if config.jwt.secret_key else '未配置'}")
    print(f"CORS 源: {len(config.cors.origins)} 个")

    if validation['warnings']:
        print(f"\n⚠️  警告:")
        for w in validation['warnings']:
            print(f"   - {w}")

    if validation['errors']:
        print(f"\n❌ 错误:")
        for e in validation['errors']:
            print(f"   - {e}")

    print(f"{'='*50}\n")


# 便捷函数
def create_flask_config(config: AppConfig) -> Dict[str, Any]:
    """创建 Flask 配置字典"""
    return {
        'SECRET_KEY': config.jwt.secret_key,
        'SQLALCHEMY_DATABASE_URI': config.database.get_uri(),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ECHO': config.debug,
        'DEBUG': config.debug,
    }
