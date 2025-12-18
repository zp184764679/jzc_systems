"""
P2-18: 跨系统服务调用重试机制

提供带有自动重试功能的 HTTP 客户端，用于跨系统 API 调用。
支持指数退避、可配置重试次数和可重试错误类型。
"""

import time
import logging
import requests
from functools import wraps
from typing import Optional, Dict, Any, Callable, Tuple, Set

# 配置日志
logger = logging.getLogger('http_client')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [HTTP-Client] %(levelname)s: %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 默认配置
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 0.5  # 初始延迟（秒）
DEFAULT_MAX_DELAY = 10  # 最大延迟（秒）
DEFAULT_BACKOFF_FACTOR = 2  # 指数退避因子
DEFAULT_TIMEOUT = 10  # 默认超时（秒）

# 可重试的 HTTP 状态码
RETRYABLE_STATUS_CODES: Set[int] = {408, 429, 500, 502, 503, 504}

# 可重试的异常类型
RETRYABLE_EXCEPTIONS: Tuple = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


def calculate_delay(attempt: int, initial_delay: float, max_delay: float, backoff_factor: float) -> float:
    """
    计算指数退避延迟时间

    Args:
        attempt: 当前重试次数（从0开始）
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        backoff_factor: 退避因子

    Returns:
        延迟时间（秒）
    """
    delay = initial_delay * (backoff_factor ** attempt)
    return min(delay, max_delay)


def should_retry(response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
    """
    判断是否应该重试

    Args:
        response: HTTP 响应对象
        exception: 发生的异常

    Returns:
        是否应该重试
    """
    if exception is not None:
        return isinstance(exception, RETRYABLE_EXCEPTIONS)

    if response is not None:
        return response.status_code in RETRYABLE_STATUS_CODES

    return False


def request_with_retry(
    method: str,
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    timeout: int = DEFAULT_TIMEOUT,
    on_retry: Optional[Callable[[int, str, Exception], None]] = None,
    **kwargs
) -> requests.Response:
    """
    带重试功能的 HTTP 请求

    Args:
        method: HTTP 方法（GET, POST, PUT, DELETE 等）
        url: 请求 URL
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        backoff_factor: 指数退避因子
        timeout: 请求超时（秒）
        on_retry: 重试回调函数，接收 (attempt, url, exception) 参数
        **kwargs: 传递给 requests 的其他参数

    Returns:
        requests.Response 对象

    Raises:
        requests.exceptions.RequestException: 所有重试都失败后抛出最后一个异常
    """
    # 设置默认超时
    if 'timeout' not in kwargs:
        kwargs['timeout'] = timeout

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)

            # 检查是否需要重试
            if should_retry(response, None) and attempt < max_retries:
                delay = calculate_delay(attempt, initial_delay, max_delay, backoff_factor)
                logger.warning(
                    f"[重试 {attempt + 1}/{max_retries}] {method} {url} "
                    f"返回状态码 {response.status_code}，{delay:.1f}秒后重试"
                )
                if on_retry:
                    on_retry(attempt + 1, url, None)
                time.sleep(delay)
                continue

            return response

        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e

            if attempt < max_retries:
                delay = calculate_delay(attempt, initial_delay, max_delay, backoff_factor)
                logger.warning(
                    f"[重试 {attempt + 1}/{max_retries}] {method} {url} "
                    f"发生异常: {type(e).__name__}: {str(e)}，{delay:.1f}秒后重试"
                )
                if on_retry:
                    on_retry(attempt + 1, url, e)
                time.sleep(delay)
            else:
                logger.error(
                    f"[重试失败] {method} {url} 所有重试均失败，"
                    f"最后一个错误: {type(e).__name__}: {str(e)}"
                )

    # 所有重试都失败，抛出最后一个异常
    if last_exception:
        raise last_exception

    return response


def get_with_retry(url: str, **kwargs) -> requests.Response:
    """带重试的 GET 请求"""
    return request_with_retry('GET', url, **kwargs)


def post_with_retry(url: str, **kwargs) -> requests.Response:
    """带重试的 POST 请求"""
    return request_with_retry('POST', url, **kwargs)


def put_with_retry(url: str, **kwargs) -> requests.Response:
    """带重试的 PUT 请求"""
    return request_with_retry('PUT', url, **kwargs)


def delete_with_retry(url: str, **kwargs) -> requests.Response:
    """带重试的 DELETE 请求"""
    return request_with_retry('DELETE', url, **kwargs)


def retry_on_failure(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    reraise: bool = True
):
    """
    重试装饰器，用于装饰包含 HTTP 调用的函数

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        backoff_factor: 指数退避因子
        reraise: 是否在所有重试失败后重新抛出异常

    Example:
        @retry_on_failure(max_retries=3)
        def get_customers():
            response = requests.get(f"{CRM_URL}/customers")
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    last_exception = e

                    if attempt < max_retries:
                        delay = calculate_delay(attempt, initial_delay, max_delay, backoff_factor)
                        logger.warning(
                            f"[重试 {attempt + 1}/{max_retries}] {func.__name__} "
                            f"发生异常: {type(e).__name__}: {str(e)}，{delay:.1f}秒后重试"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[重试失败] {func.__name__} 所有重试均失败，"
                            f"最后一个错误: {type(e).__name__}: {str(e)}"
                        )
                        if reraise:
                            raise

            return None

        return wrapper
    return decorator


class RetryableHTTPClient:
    """
    可配置的 HTTP 客户端类

    Example:
        client = RetryableHTTPClient(
            base_url="http://localhost:8002",
            max_retries=3,
            timeout=15
        )
        response = client.get("/api/customers")
        data = response.json()
    """

    def __init__(
        self,
        base_url: str = "",
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        timeout: int = DEFAULT_TIMEOUT,
        default_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.default_headers = default_headers or {}

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """合并默认头和自定义头"""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """发送请求"""
        url = self._build_url(path)
        merged_headers = self._merge_headers(headers)

        return request_with_retry(
            method=method,
            url=url,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            backoff_factor=self.backoff_factor,
            timeout=self.timeout,
            headers=merged_headers,
            **kwargs
        )

    def get(self, path: str, **kwargs) -> requests.Response:
        """GET 请求"""
        return self.request('GET', path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        """POST 请求"""
        return self.request('POST', path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        """PUT 请求"""
        return self.request('PUT', path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        return self.request('DELETE', path, **kwargs)

    def safe_get(self, path: str, default: Any = None, **kwargs) -> Any:
        """
        安全 GET 请求，发生错误时返回默认值而不是抛出异常
        """
        try:
            response = self.get(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"safe_get 失败: {path}, 错误: {str(e)}")
            return default

    def safe_post(self, path: str, default: Any = None, **kwargs) -> Any:
        """
        安全 POST 请求，发生错误时返回默认值而不是抛出异常
        """
        try:
            response = self.post(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"safe_post 失败: {path}, 错误: {str(e)}")
            return default


# 预配置的客户端工厂函数
def create_service_client(
    service_name: str,
    base_url: str,
    **kwargs
) -> RetryableHTTPClient:
    """
    创建服务客户端

    Args:
        service_name: 服务名称（用于日志）
        base_url: 服务基础 URL
        **kwargs: 传递给 RetryableHTTPClient 的其他参数

    Returns:
        配置好的 RetryableHTTPClient 实例
    """
    client = RetryableHTTPClient(base_url=base_url, **kwargs)
    logger.info(f"创建 {service_name} 服务客户端: {base_url}")
    return client
