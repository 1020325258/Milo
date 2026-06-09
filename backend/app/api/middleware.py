"""
API 中间件

提供错误处理、请求日志等中间件。
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            响应对象
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"未处理的异常: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "内部服务器错误"},
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            响应对象
        """
        start_time = time.time()

        # 记录请求
        logger.info(f"请求开始: {request.method} {request.url.path}")

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        process_time = time.time() - start_time

        # 记录响应
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"状态码={response.status_code} 耗时={process_time:.3f}s"
        )

        # 添加耗时 header
        response.headers["X-Process-Time"] = str(process_time)

        return response
