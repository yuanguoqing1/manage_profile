"""记忆管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.memory_service import (
    add_memory,
    get_all_memories,
    clear_user_memories,
    is_memory_enabled,
)

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryAddRequest(BaseModel):
    content: str


class MemoryResponse(BaseModel):
    success: bool
    message: str


class MemoriesListResponse(BaseModel):
    enabled: bool
    memories: list[str]


@router.get("/status")
def get_memory_status(user: User = Depends(get_current_user)) -> dict:
    """获取记忆服务状态。"""
    return {
        "enabled": is_memory_enabled(),
        "user_id": user.id,
    }


@router.get("/list", response_model=MemoriesListResponse)
def list_memories(user: User = Depends(get_current_user)) -> MemoriesListResponse:
    """获取当前用户的所有记忆。"""
    if not is_memory_enabled():
        return MemoriesListResponse(enabled=False, memories=[])
    
    memories = get_all_memories(str(user.id))
    return MemoriesListResponse(enabled=True, memories=memories)


@router.post("/add", response_model=MemoryResponse)
def add_user_memory(
    request: MemoryAddRequest,
    user: User = Depends(get_current_user),
) -> MemoryResponse:
    """手动添加记忆。"""
    if not is_memory_enabled():
        raise HTTPException(status_code=503, detail="记忆服务未启用")
    
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="记忆内容不能为空")
    
    success = add_memory(request.content, str(user.id))
    if success:
        return MemoryResponse(success=True, message="记忆已添加")
    else:
        raise HTTPException(status_code=500, detail="添加记忆失败")


@router.delete("/clear", response_model=MemoryResponse)
def clear_memories(user: User = Depends(get_current_user)) -> MemoryResponse:
    """清空当前用户的所有记忆。"""
    if not is_memory_enabled():
        raise HTTPException(status_code=503, detail="记忆服务未启用")
    
    success = clear_user_memories(str(user.id))
    if success:
        return MemoryResponse(success=True, message="记忆已清空")
    else:
        raise HTTPException(status_code=500, detail="清空记忆失败")
