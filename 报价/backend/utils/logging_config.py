# utils/logging_config.py
"""
统一日志配置
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logging(
    app_name: str = "quotation",
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True
):
    """
    配置应用日志

    Args:
        app_name: 应用名称
        log_level: 日志级别
        log_dir: 日志目录
        enable_file_logging: 是否启用文件日志
        enable_console_logging: 是否启用控制台日志
    """

    # 创建日志目录
    if enable_file_logging:
        Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 获取根logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的handlers
    logger.handlers.clear()

    # 日志格式
    detailed_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_format = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # 控制台处理器
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_format)
        logger.addHandler(console_handler)

    # 文件处理器
    if enable_file_logging:
        # 通用日志文件
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_format)
        logger.addHandler(file_handler)

        # 错误日志文件
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}_error.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_format)
        logger.addHandler(error_handler)

    # 配置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)

    logger.info(f"✅ 日志系统初始化完成: {app_name}")
    logger.info(f"   日志级别: {log_level}")
    if enable_file_logging:
        logger.info(f"   日志目录: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称

    Returns:
        logging.Logger实例
    """
    return logging.getLogger(name)


class RequestLogger:
    """请求日志记录器（中间件）"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api.requests")

    async def __call__(self, request, call_next):
        # 记录请求
        start_time = datetime.now()

        self.logger.info(
            f"📨 {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # 处理请求
        response = await call_next(request)

        # 记录响应
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"📤 {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration:.3f}s)"
        )

        return response


# 安全日志函数
def log_security_event(event_type: str, details: dict, severity: str = "INFO"):
    """
    记录安全事件

    Args:
        event_type: 事件类型（如：login_failed, unauthorized_access）
        details: 事件详情
        severity: 严重程度
    """
    logger = get_logger("security")

    log_message = f"🔒 安全事件: {event_type}"
    for key, value in details.items():
        log_message += f" | {key}={value}"

    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(level, log_message)


# 业务日志函数
def log_business_event(event_type: str, user_id: str, details: dict):
    """
    记录业务事件

    Args:
        event_type: 事件类型（如：quote_created, drawing_uploaded）
        user_id: 用户ID
        details: 事件详情
    """
    logger = get_logger("business")

    log_message = f"💼 业务事件: {event_type} | user={user_id}"
    for key, value in details.items():
        log_message += f" | {key}={value}"

    logger.info(log_message)
