"""Web 页面和分类管理路由。"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User, WebCategory, WebPage
from app.schemas.user import (
    WebCategoryCreate,
    WebCategoryPublic,
    WebPageCreate,
    WebPagePublic,
)

router = APIRouter(prefix="/web", tags=["web"])


# ==================== 分类管理 ====================

@router.get("/categories", response_model=list[WebCategoryPublic])
def list_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有分类。"""
    categories = session.exec(
        select(WebCategory).where(WebCategory.user_id == current_user.id)
    ).all()
    return categories


@router.post("/categories", response_model=WebCategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: WebCategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建新分类。"""
    # 检查当前用户的分类名是否已存在
    existing = session.exec(
        select(WebCategory).where(
            WebCategory.name == payload.name,
            WebCategory.user_id == current_user.id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名已存在")

    category = WebCategory(**payload.model_dump(), user_id=current_user.id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=WebCategoryPublic)
def update_category(
    category_id: int,
    payload: WebCategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """更新分类。"""
    category = session.get(WebCategory, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查新名称是否与其他分类冲突
    if payload.name != category.name:
        existing = session.exec(
            select(WebCategory).where(
                WebCategory.name == payload.name,
                WebCategory.user_id == current_user.id
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="分类名已存在")

    for key, value in payload.model_dump().items():
        setattr(category, key, value)
    
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除分类。"""
    category = session.get(WebCategory, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 删除该分类下的所有页面
    pages = session.exec(
        select(WebPage).where(WebPage.category_id == category_id)
    ).all()
    for page in pages:
        session.delete(page)

    session.delete(category)
    session.commit()
    return None


# ==================== 页面管理 ====================

@router.get("/pages", response_model=list[WebPagePublic])
def list_pages(
    category_id: Optional[int] = Query(None, description="按分类 ID 筛选"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的页面列表，可选按分类筛选。"""
    query = select(WebPage).where(WebPage.user_id == current_user.id)
    if category_id is not None:
        query = query.where(WebPage.category_id == category_id)
    
    pages = session.exec(query).all()
    return pages


@router.post("/pages", response_model=WebPagePublic, status_code=status.HTTP_201_CREATED)
def create_page(
    payload: WebPageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建新页面。"""
    # 验证分类是否存在且属于当前用户
    category = session.get(WebCategory, payload.category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="分类不存在")

    page = WebPage(**payload.model_dump(), user_id=current_user.id)
    session.add(page)
    session.commit()
    session.refresh(page)
    return page


@router.put("/pages/{page_id}", response_model=WebPagePublic)
def update_page(
    page_id: int,
    payload: WebPageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """更新页面。"""
    page = session.get(WebPage, page_id)
    if not page or page.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="页面不存在")

    # 如果更改了分类，验证新分类是否存在且属于当前用户
    if payload.category_id != page.category_id:
        category = session.get(WebCategory, payload.category_id)
        if not category or category.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="分类不存在")

    for key, value in payload.model_dump().items():
        setattr(page, key, value)
    
    session.add(page)
    session.commit()
    session.refresh(page)
    return page


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    page_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除页面。"""
    page = session.get(WebPage, page_id)
    if not page or page.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="页面不存在")

    session.delete(page)
    session.commit()
    return None
