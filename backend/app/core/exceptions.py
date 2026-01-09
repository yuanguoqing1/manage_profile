"""自定义异常类。"""

from __future__ import annotations


class AppException(Exception):
    """应用基础异常。"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AppException):
    """认证失败异常。"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401)


class AuthorizationError(AppException):
    """授权失败异常。"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(AppException):
    """资源不存在异常。"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """数据验证失败异常。"""

    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message, status_code=400)


class RateLimitError(AppException):
    """请求频率限制异常。"""

    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, status_code=429)


class NetworkError(AppException):
    """网络连接错误异常。"""

    def __init__(self, message: str = "网络连接失败，请检查网络设置"):
        super().__init__(message, status_code=503)


class API12306Error(AppException):
    """12306 API错误异常。"""

    def __init__(self, message: str = "12306接口返回错误", status_code: int = 502):
        super().__init__(message, status_code=status_code)


class DataParseError(AppException):
    """数据解析错误异常。"""

    def __init__(self, message: str = "数据解析失败"):
        super().__init__(message, status_code=500)
