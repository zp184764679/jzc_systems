# utils/error_handler.py
"""
统一错误处理工具
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
import logging
from typing import Union
import traceback

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseException(BusinessException):
    """数据库异常"""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR", 500)


class ValidationException(BusinessException):
    """验证异常"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class NotFoundException(BusinessException):
    """资源未找到异常"""
    def __init__(self, resource: str, resource_id: Union[int, str]):
        message = f"{resource} ID={resource_id} 不存在"
        super().__init__(message, "NOT_FOUND", 404)


def format_error_response(
    message: str,
    code: str = "ERROR",
    details: dict = None,
    status_code: int = 500
) -> dict:
    """格式化错误响应"""
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }

    if details:
        response["error"]["details"] = details

    return response


async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(f"业务异常: {exc.code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            message=exc.message,
            code=exc.code,
            status_code=exc.status_code
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"请求验证失败: {errors}")

    return JSONResponse(
        status_code=422,
        content=format_error_response(
            message="请求参数验证失败",
            code="VALIDATION_ERROR",
            details={"errors": errors},
            status_code=422
        )
    )


async def database_exception_handler(request: Request, exc: IntegrityError):
    """数据库完整性异常处理器"""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

    # 检测常见的数据库错误
    if "UNIQUE constraint" in error_msg or "Duplicate entry" in error_msg:
        message = "数据已存在，请检查唯一字段"
        code = "DUPLICATE_ERROR"
    elif "FOREIGN KEY constraint" in error_msg:
        message = "关联数据不存在或已被引用"
        code = "FOREIGN_KEY_ERROR"
    else:
        message = "数据库操作失败"
        code = "DATABASE_ERROR"

    logger.error(f"数据库错误: {error_msg}")

    return JSONResponse(
        status_code=400,
        content=format_error_response(
            message=message,
            code=code,
            status_code=400
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    # 记录详细错误信息
    error_traceback = traceback.format_exc()
    logger.error(f"未处理的异常: {type(exc).__name__}")
    logger.error(f"错误信息: {str(exc)}")
    logger.error(f"堆栈跟踪:\n{error_traceback}")

    # 根据不同异常类型返回不同消息
    if isinstance(exc, OperationalError):
        message = "数据库连接失败，请稍后重试"
        code = "DATABASE_CONNECTION_ERROR"
    elif isinstance(exc, ValueError):
        message = "参数值错误"
        code = "VALUE_ERROR"
    else:
        message = "服务器内部错误，请联系管理员"
        code = "INTERNAL_SERVER_ERROR"

    return JSONResponse(
        status_code=500,
        content=format_error_response(
            message=message,
            code=code,
            status_code=500
        )
    )


def handle_api_error(func):
    """API错误处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BusinessException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except IntegrityError as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            logger.error(f"数据库完整性错误: {error_msg}")

            if "UNIQUE constraint" in error_msg or "Duplicate entry" in error_msg:
                raise HTTPException(status_code=400, detail="数据已存在")
            else:
                raise HTTPException(status_code=500, detail="数据库操作失败")
        except Exception as e:
            logger.error(f"API错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")

    return wrapper
