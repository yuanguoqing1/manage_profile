"""AI记忆服务 - 基于powermem为每个用户提供独立记忆存储。"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# 全局记忆实例
_memory_instance = None
_memory_enabled = False


def init_memory():
    """初始化记忆服务。"""
    global _memory_instance, _memory_enabled
    
    try:
        from powermem import Memory
        
        # 从环境变量读取配置
        api_key = os.getenv('POWERMEM_LLM_API_KEY', '')
        base_url = os.getenv('POWERMEM_LLM_BASE_URL', '')
        model = os.getenv('POWERMEM_LLM_MODEL', 'mimo-v2-flash')
        
        if not api_key:
            logger.warning("POWERMEM_LLM_API_KEY 未配置，AI记忆功能已禁用")
            _memory_enabled = False
            return
        
        # 使用字典配置
        config = {
            'llm': {
                'provider': 'openai',
                'config': {
                    'api_key': api_key,
                    'base_url': base_url,
                    'model': model,
                    'temperature': 0.7
                }
            },
            'embedder': {
                'provider': 'openai',
                'config': {
                    'api_key': api_key,
                    'base_url': base_url,
                    'model': model
                }
            },
            'vector_store': {
                'provider': 'sqlite',
                'config': {
                    'path': os.getenv('POWERMEM_VECTOR_STORE_PATH', './powermem.db')
                }
            }
        }
        
        _memory_instance = Memory(config=config)
        _memory_enabled = True
        logger.info("AI记忆服务初始化成功")
    except ImportError:
        logger.warning("powermem未安装，AI记忆功能已禁用。请运行: pip install powermem")
        _memory_enabled = False
    except Exception as e:
        logger.warning(f"AI记忆服务初始化失败: {e}")
        _memory_enabled = False


def is_memory_enabled() -> bool:
    """检查记忆服务是否可用。"""
    return _memory_enabled and _memory_instance is not None


def add_memory(content: str, user_id: str, metadata: Optional[dict] = None) -> bool:
    """
    为用户添加记忆。
    
    Args:
        content: 记忆内容
        user_id: 用户ID
        metadata: 可选的元数据
    
    Returns:
        是否添加成功
    """
    if not is_memory_enabled():
        return False
    
    try:
        _memory_instance.add(content, user_id=str(user_id), metadata=metadata or {})
        logger.debug(f"为用户 {user_id} 添加记忆: {content[:50]}...")
        return True
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        return False


def search_memories(query: str, user_id: str, limit: int = 5) -> list[str]:
    """
    搜索用户相关记忆。
    
    Args:
        query: 搜索查询
        user_id: 用户ID
        limit: 返回结果数量限制
    
    Returns:
        相关记忆列表
    """
    if not is_memory_enabled():
        return []
    
    try:
        results = _memory_instance.search(query, user_id=str(user_id), limit=limit)
        memories = []
        for result in results.get('results', []):
            memory_text = result.get('memory', '')
            if memory_text:
                memories.append(memory_text)
        return memories
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        return []


def get_all_memories(user_id: str) -> list[str]:
    """
    获取用户所有记忆。
    
    Args:
        user_id: 用户ID
    
    Returns:
        记忆列表
    """
    if not is_memory_enabled():
        return []
    
    try:
        results = _memory_instance.get_all(user_id=str(user_id))
        memories = []
        for result in results.get('results', []):
            memory_text = result.get('memory', '')
            if memory_text:
                memories.append(memory_text)
        return memories
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        return []


def delete_memory(memory_id: str, user_id: str) -> bool:
    """
    删除指定记忆。
    
    Args:
        memory_id: 记忆ID
        user_id: 用户ID
    
    Returns:
        是否删除成功
    """
    if not is_memory_enabled():
        return False
    
    try:
        _memory_instance.delete(memory_id, user_id=str(user_id))
        return True
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        return False


def clear_user_memories(user_id: str) -> bool:
    """
    清空用户所有记忆。
    
    Args:
        user_id: 用户ID
    
    Returns:
        是否清空成功
    """
    if not is_memory_enabled():
        return False
    
    try:
        _memory_instance.delete_all(user_id=str(user_id))
        logger.info(f"已清空用户 {user_id} 的所有记忆")
        return True
    except Exception as e:
        logger.error(f"清空记忆失败: {e}")
        return False


def extract_and_save_memory(user_message: str, assistant_response: str, user_id: str) -> None:
    """
    从对话中提取并保存重要记忆。
    
    Args:
        user_message: 用户消息
        assistant_response: AI回复
        user_id: 用户ID
    """
    if not is_memory_enabled():
        return
    
    # 简单的记忆提取规则
    memory_keywords = [
        '我喜欢', '我不喜欢', '我是', '我的', '我叫', '我住在',
        '我工作', '我学习', '我经常', '我习惯', '我偏好',
        '记住', '请记住', '别忘了', '提醒我'
    ]
    
    for keyword in memory_keywords:
        if keyword in user_message:
            # 保存包含关键词的用户消息作为记忆
            add_memory(user_message, user_id)
            break
