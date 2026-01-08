"""技能库路由。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import Skill, User
from app.schemas.user import SkillCreate, SkillPublic, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillPublic])
def list_skills(
    category: str | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取技能列表（支持按分类筛选，只返回当前用户的数据）。"""
    query = select(Skill).where(Skill.user_id == current_user.id)
    if category:
        query = query.where(Skill.category == category)
    skills = session.exec(query.order_by(Skill.updated_at.desc())).all()
    return skills


@router.get("/categories")
def list_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有分类。"""
    skills = session.exec(select(Skill).where(Skill.user_id == current_user.id)).all()
    categories = list(set(skill.category for skill in skills))
    return {"categories": sorted(categories)}


@router.get("/{skill_id}", response_model=SkillPublic)
def get_skill(
    skill_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取单个技能详情（只能查看自己的）。"""
    skill = session.get(Skill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


@router.post("", response_model=SkillPublic, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建新技能（所有登录用户可用）。"""
    now = datetime.now().isoformat()
    skill = Skill(
        title=payload.title,
        category=payload.category,
        content=payload.content,
        tags=payload.tags,
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=SkillPublic)
def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """更新技能（只能更新自己的）。"""
    skill = session.get(Skill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="技能不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(skill, key, value)
    
    skill.updated_at = datetime.now().isoformat()
    
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除技能（只能删除自己的）。"""
    skill = session.get(Skill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="技能不存在")
    
    session.delete(skill)
    session.commit()
    return None
