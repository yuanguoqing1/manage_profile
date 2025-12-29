"""简单的内存限流中间件。"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于内存的简单限流中间件。
    
    生产环境建议使用 Redis 实现分布式限流。
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        """初始化限流中间件。
        
        Args:
            app: FastAPI 应用实例
            calls: 时间窗口内允许的最大请求数
            period: 时间窗口（秒）
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查、文档端点和 OPTIONS 请求
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"] or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 清理过期的请求记录
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip] if now - timestamp < self.period
        ]

        # 检查是否超过限流
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请在 {self.period} 秒后重试",
            )

        # 记录本次请求
        self.clients[client_ip].append(now)

        return await call_next(request)
