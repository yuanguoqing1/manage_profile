"""角色提示词管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import RolePrompt, User
from app.schemas.user import RolePromptCreate, RolePromptPublic, RolePromptUpdate

router = APIRouter(prefix="/role-prompts", tags=["role-prompts"])


@router.get("", response_model=list[RolePromptPublic])
def list_role_prompts(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """获取所有角色提示词。"""
    prompts = session.exec(select(RolePrompt)).all()
    return prompts


@router.post("", response_model=RolePromptPublic, status_code=status.HTTP_201_CREATED)
def create_role_prompt(
    payload: RolePromptCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """创建新角色提示词（仅管理员）。"""
    # 检查名称是否已存在
    existing = session.exec(
        select(RolePrompt).where(RolePrompt.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色名称已存在")

    prompt = RolePrompt(**payload.model_dump())
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    return prompt


@router.put("/{prompt_id}", response_model=RolePromptPublic)
def update_role_prompt(
    prompt_id: int,
    payload: RolePromptUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """更新角色提示词（仅管理员）。"""
    prompt = session.get(RolePrompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="角色提示词不存在")

    update_data = payload.model_dump(exclude_unset=True)
    
    # 如果更新名称，检查是否与其他角色冲突
    if "name" in update_data and update_data["name"] != prompt.name:
        existing = session.exec(
            select(RolePrompt).where(RolePrompt.name == update_data["name"])
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="角色名称已存在")

    for key, value in update_data.items():
        setattr(prompt, key, value)
    
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role_prompt(
    prompt_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """删除角色提示词（仅管理员）。"""
    prompt = session.get(RolePrompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="角色提示词不存在")

    session.delete(prompt)
    session.commit()
    return None
