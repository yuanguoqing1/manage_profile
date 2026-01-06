"""GitHub 热点项目路由。"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.github_service import TrendingProject, get_trending_python_projects

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["github"])


class TrendingResponse(BaseModel):
    """热门项目响应模型"""
    projects: list[TrendingProject]
    cached: bool
    updated_at: str


@router.get("/trending", response_model=TrendingResponse)
async def get_trending_projects():
    """获取热门 Python 项目列表
    
    Returns:
        TrendingResponse: 包含项目列表、缓存状态和更新时间
        
    Raises:
        HTTPException: 获取数据失败时返回 500 或 503 错误
    """
    try:
        projects, cached = await get_trending_python_projects(limit=30)
        
        return TrendingResponse(
            projects=projects,
            cached=cached,
            updated_at=datetime.now().isoformat()
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取热门项目失败: {error_msg}")
        
        # 根据错误类型返回不同的状态码
        if "频率超限" in error_msg or "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API 请求频率超限，请稍后重试"
            )
        elif "超时" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub API 请求超时"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取 GitHub 数据失败"
            )
