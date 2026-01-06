"""GitHub 热点项目服务 - 获取热门 Python 项目"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
import redis
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import engine
from app.models.user import ModelConfig

logger = logging.getLogger(__name__)

# Redis 缓存配置
CACHE_KEY = "github:trending:python"
CACHE_TTL = 3600  # 1 小时

# GitHub API 配置
GITHUB_API_URL = "https://api.github.com/search/repositories"


class TrendingProject(BaseModel):
    """热门项目数据模型"""
    name: str
    full_name: str
    description: Optional[str] = None
    description_cn: Optional[str] = None  # 中文描述
    stars: int
    forks: int
    url: str
    author: str
    language: str
    created_at: str
    updated_at: str


def _get_redis_client() -> Optional[redis.Redis]:
    """获取 Redis 客户端"""
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis 连接失败，将直接请求 GitHub API: {e}")
        return None


def _build_search_query() -> str:
    """构建 GitHub 搜索查询字符串
    
    搜索当月创建或更新的 Python 项目
    """
    # 获取当月第一天
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    date_str = first_day_of_month.strftime("%Y-%m-%d")
    
    # 构建查询：Python 语言，当月更新，按星标排序
    query = f"language:python pushed:>={date_str}"
    return query


async def _fetch_from_github(query: str, limit: int) -> list[dict]:
    """从 GitHub API 获取数据
    
    Args:
        query: 搜索查询字符串
        limit: 返回项目数量
        
    Returns:
        GitHub API 返回的仓库列表
        
    Raises:
        httpx.HTTPStatusError: API 请求失败
        httpx.TimeoutException: 请求超时
    """
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Trending-App"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GITHUB_API_URL,
            params=params,
            headers=headers,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])


def _transform_to_trending_project(repo: dict) -> TrendingProject:
    """将 GitHub API 响应转换为 TrendingProject 对象
    
    Args:
        repo: GitHub API 返回的仓库数据
        
    Returns:
        TrendingProject 对象
    """
    return TrendingProject(
        name=repo.get("name", ""),
        full_name=repo.get("full_name", ""),
        description=repo.get("description"),
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        url=repo.get("html_url", ""),
        author=repo.get("owner", {}).get("login", ""),
        language=repo.get("language", "Python"),
        created_at=repo.get("created_at", ""),
        updated_at=repo.get("updated_at", "")
    )


def _get_cached_projects(redis_client: redis.Redis) -> Optional[list[TrendingProject]]:
    """从 Redis 获取缓存数据
    
    Args:
        redis_client: Redis 客户端
        
    Returns:
        缓存的项目列表，如果缓存不存在或过期则返回 None
    """
    try:
        cached_data = redis_client.get(CACHE_KEY)
        if cached_data:
            projects_data = json.loads(cached_data)
            return [TrendingProject(**p) for p in projects_data]
    except Exception as e:
        logger.warning(f"读取 Redis 缓存失败: {e}")
    return None


def _cache_projects(redis_client: redis.Redis, projects: list[TrendingProject]) -> None:
    """将项目数据缓存到 Redis
    
    Args:
        redis_client: Redis 客户端
        projects: 项目列表
    """
    try:
        projects_data = [p.model_dump() for p in projects]
        redis_client.setex(
            CACHE_KEY,
            CACHE_TTL,
            json.dumps(projects_data, ensure_ascii=False)
        )
        logger.info(f"已缓存 {len(projects)} 个热门项目到 Redis")
    except Exception as e:
        logger.warning(f"写入 Redis 缓存失败: {e}")


async def _translate_descriptions(projects: list[TrendingProject]) -> list[TrendingProject]:
    """使用配置的大模型翻译项目描述
    
    Args:
        projects: 项目列表
        
    Returns:
        带有中文描述的项目列表
    """
    # 获取所有可用模型
    with Session(engine) as session:
        all_models = list(session.exec(select(ModelConfig)).all())
        if not all_models:
            logger.warning("未配置大模型，跳过翻译")
            return projects
    
    # 收集需要翻译的描述
    descriptions_to_translate = []
    for i, p in enumerate(projects):
        if p.description and not p.description_cn:
            descriptions_to_translate.append((i, p.description))
    
    if not descriptions_to_translate:
        return projects
    
    # 批量翻译（每次5个，避免请求过大）
    batch_size = 5
    for batch_start in range(0, len(descriptions_to_translate), batch_size):
        batch = descriptions_to_translate[batch_start:batch_start + batch_size]
        
        # 构建翻译提示
        texts = "\n".join([f"{i+1}. {desc[:200]}" for i, (_, desc) in enumerate(batch)])  # 限制每个描述长度
        prompt = f"""将以下GitHub项目描述翻译成中文，每行一个，格式"序号. 翻译"：

{texts}"""
        
        # 尝试所有模型
        success = False
        for model in all_models:
            if success:
                break
                
            # 重试机制
            for retry in range(2):
                try:
                    # 如果 base_url 已包含 /chat/completions 则直接使用，否则拼接
                    if 'chat/completions' in model.base_url:
                        target_url = model.base_url
                    else:
                        target_url = f"{model.base_url.rstrip('/')}/chat/completions"
                    request_body = {
                        "model": model.model_name,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3,
                    }
                    
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            target_url,
                            headers={"Authorization": f"Bearer {model.api_key}"},
                            json=request_body,
                        )
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                            except Exception as json_err:
                                logger.warning(f"模型 {model.name} 返回非 JSON 响应: {response.text[:200]}")
                                break  # 尝试下一个模型
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            
                            # 解析翻译结果
                            lines = content.strip().split("\n")
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                # 尝试解析 "1. 翻译内容" 格式
                                if ". " in line:
                                    try:
                                        num_str, translation = line.split(". ", 1)
                                        num = int(num_str.strip()) - 1
                                        if 0 <= num < len(batch):
                                            original_idx = batch[num][0]
                                            projects[original_idx].description_cn = translation.strip()
                                    except (ValueError, IndexError):
                                        continue
                            success = True
                            break  # 成功则跳出重试循环
                        elif response.status_code in (429, 502, 503, 404):
                            logger.warning(f"模型 {model.name} 返回 {response.status_code}，响应: {response.text[:200]}")
                            break  # 跳出重试，尝试下一个模型
                        else:
                            logger.warning(f"翻译请求失败: {response.status_code}, 重试 {retry + 1}/2")
                            
                except Exception as e:
                    logger.warning(f"翻译过程出错: {e}, 重试 {retry + 1}/2")
                    continue
        
        if not success:
            logger.warning("所有模型翻译失败，跳过此批次")
    
    return projects


async def get_trending_python_projects(limit: int = 30) -> tuple[list[TrendingProject], bool]:
    """获取热门 Python 项目
    
    优先从 Redis 缓存获取，缓存未命中则从 GitHub API 获取
    
    Args:
        limit: 返回项目数量，默认30
        
    Returns:
        元组 (项目列表, 是否来自缓存)
        
    Raises:
        Exception: 获取数据失败时抛出异常
    """
    redis_client = _get_redis_client()
    
    # 尝试从缓存获取
    if redis_client:
        cached_projects = _get_cached_projects(redis_client)
        if cached_projects:
            logger.info(f"从 Redis 缓存返回 {len(cached_projects)} 个热门项目")
            return cached_projects, True
    
    # 缓存未命中，从 GitHub API 获取
    logger.info("缓存未命中，正在从 GitHub API 获取热门项目...")
    
    try:
        query = _build_search_query()
        repos = await _fetch_from_github(query, limit)
        
        # 转换为 TrendingProject 对象
        projects = [_transform_to_trending_project(repo) for repo in repos]
        
        # 使用大模型翻译描述
        logger.info("正在翻译项目描述...")
        projects = await _translate_descriptions(projects)
        
        # 缓存结果
        if redis_client and projects:
            _cache_projects(redis_client, projects)
        
        logger.info(f"从 GitHub API 获取了 {len(projects)} 个热门项目")
        return projects, False
        
    except httpx.TimeoutException:
        logger.error("GitHub API 请求超时")
        raise Exception("GitHub API 请求超时")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.error("GitHub API 请求频率超限")
            raise Exception("GitHub API 请求频率超限，请稍后重试")
        logger.error(f"GitHub API 返回错误: {e.response.status_code}")
        raise Exception("获取 GitHub 数据失败")
    except Exception as e:
        logger.error(f"获取热门项目失败: {e}")
        raise Exception(f"获取 GitHub 数据失败: {str(e)}")
