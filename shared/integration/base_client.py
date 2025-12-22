"""
基础集成客户端类

提供所有系统集成客户端的基础功能，包括：
- HTTP 请求（带重试）
- 统一的错误处理
- 日志记录
- 配置管理
"""

import os
import logging
from typing import Optional, Dict, Any, List
from ..http_client import RetryableHTTPClient

logger = logging.getLogger('integration')


class BaseIntegrationClient:
    """
    基础集成客户端

    所有系统特定的客户端都应继承此类。
    """

    # 子类需要设置的属性
    SERVICE_NAME: str = "base"
    ENV_URL_KEY: str = "SERVICE_URL"
    DEFAULT_URL: str = "http://localhost:8000"
    DEFAULT_TIMEOUT: int = 10
    DEFAULT_MAX_RETRIES: int = 3

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        token: Optional[str] = None
    ):
        """
        初始化客户端

        Args:
            base_url: 服务基础 URL，默认从环境变量读取
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            token: 认证 Token（可选）
        """
        self.base_url = base_url or os.getenv(self.ENV_URL_KEY, self.DEFAULT_URL)
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.token = token

        # 构建默认请求头
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # 创建 HTTP 客户端
        self._client = RetryableHTTPClient(
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
            default_headers=headers
        )

        logger.info(f"[{self.SERVICE_NAME}] 客户端初始化: {self.base_url}")

    def _get(self, path: str, params: Optional[Dict] = None, **kwargs) -> Dict:
        """
        发送 GET 请求

        Args:
            path: API 路径
            params: 查询参数
            **kwargs: 其他参数

        Returns:
            响应 JSON 数据
        """
        try:
            response = self._client.get(path, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[{self.SERVICE_NAME}] GET {path} 失败: {e}")
            raise

    def _post(self, path: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """发送 POST 请求"""
        try:
            response = self._client.post(path, json=data, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[{self.SERVICE_NAME}] POST {path} 失败: {e}")
            raise

    def _put(self, path: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """发送 PUT 请求"""
        try:
            response = self._client.put(path, json=data, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[{self.SERVICE_NAME}] PUT {path} 失败: {e}")
            raise

    def _delete(self, path: str, **kwargs) -> Dict:
        """发送 DELETE 请求"""
        try:
            response = self._client.delete(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[{self.SERVICE_NAME}] DELETE {path} 失败: {e}")
            raise

    def _safe_get(self, path: str, default: Any = None, params: Optional[Dict] = None) -> Any:
        """
        安全的 GET 请求，错误时返回默认值
        """
        try:
            return self._get(path, params=params)
        except Exception as e:
            logger.warning(f"[{self.SERVICE_NAME}] safe_get {path} 失败，返回默认值: {e}")
            return default

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否健康
        """
        try:
            response = self._client.get("/health", timeout=5, max_retries=1)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"[{self.SERVICE_NAME}] 健康检查失败: {e}")
            return False
