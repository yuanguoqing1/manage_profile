from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.diary import Diary, DiaryCreate, DiaryRead, DiaryUpdate
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[DiaryRead])
def get_diaries(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有日记"""
    statement = select(Diary).where(Diary.user_id == current_user.id).order_by(Diary.created_at.desc())
    return session.exec(statement).all()


@router.post("", response_model=DiaryRead)
def create_diary(
    diary_in: DiaryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建新日记"""
    diary = Diary(
        **diary_in.dict(),
        user_id=current_user.id,
    )
    session.add(diary)
    session.commit()
    session.refresh(diary)
    return diary


@router.get("/{diary_id}", response_model=DiaryRead)
def get_diary(
    diary_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取单篇日记"""
    diary = session.get(Diary, diary_id)
    if not diary or diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="日记不存在")
    return diary


@router.put("/{diary_id}", response_model=DiaryRead)
def update_diary(
    diary_id: int,
    diary_in: DiaryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """更新日记"""
    diary = session.get(Diary, diary_id)
    if not diary or diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="日记不存在")
    
    for key, value in diary_in.dict(exclude_unset=True).items():
        setattr(diary, key, value)
    diary.updated_at = datetime.utcnow()
    
    session.add(diary)
    session.commit()
    session.refresh(diary)
    return diary


@router.delete("/{diary_id}")
def delete_diary(
    diary_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除日记"""
    diary = session.get(Diary, diary_id)
    if not diary or diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="日记不存在")
    
    session.delete(diary)
    session.commit()
    return {"message": "日记已删除"}
