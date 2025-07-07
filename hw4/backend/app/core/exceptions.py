from typing import Any, Dict, Optional
from fastapi import status

class APIException(Exception):
    """基础API异常类"""
    def __init__(
        self,
        detail: str,
        code: str = "internal_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.headers = headers
        super().__init__(detail)

class NotFoundException(APIException):
    """资源未找到异常"""
    def __init__(
        self,
        detail: str = "Resource not found",
        code: str = "not_found",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            headers=headers,
        )

class BadRequestException(APIException):
    """请求参数错误异常"""
    def __init__(
        self,
        detail: str = "Bad request",
        code: str = "bad_request",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=headers,
        )

class UnauthorizedException(APIException):
    """未授权异常"""
    def __init__(
        self,
        detail: str = "Not authenticated",
        code: str = "unauthorized",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers,
        )

class ForbiddenException(APIException):
    """禁止访问异常"""
    def __init__(
        self,
        detail: str = "Forbidden",
        code: str = "forbidden",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers,
        )

class ElasticsearchException(APIException):
    """Elasticsearch异常"""
    def __init__(
        self,
        detail: str = "Elasticsearch error",
        code: str = "elasticsearch_error",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers=headers,
        )