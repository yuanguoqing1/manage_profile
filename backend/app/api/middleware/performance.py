"""性能监控中间件。"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """性能监控中间件，记录请求响应时间。"""

    def __init__(self, app, slow_request_threshold: float = 1.0):
        """初始化性能监控中间件。
        
        Args:
            app: FastAPI 应用实例
            slow_request_threshold: 慢请求阈值（秒）
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时间
        process_time = time.time() - start_time
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            logger.warning(
                "慢请求: %s %s - %.2f秒",
                request.method,
                request.url.path,
                process_time,
            )
        
        # 记录所有请求（调试模式）
        logger.debug(
            "%s %s - %d - %.3f秒",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求信息
        logger.info(
            "请求: %s %s - 客户端: %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应信息
        logger.info(
            "响应: %s %s - 状态码: %d",
            request.method,
            request.url.path,
            response.status_code,
        )
        
        return response
