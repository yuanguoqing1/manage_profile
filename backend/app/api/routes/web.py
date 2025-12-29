"""Web 页面和分类管理路由。"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_admin
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
    _: User = Depends(get_current_user),
):
    """获取所有分类。"""
    categories = session.exec(select(WebCategory)).all()
    return categories


@router.post("/categories", response_model=WebCategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: WebCategoryCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """创建新分类（仅管理员）。"""
    # 检查分类名是否已存在
    existing = session.exec(
        select(WebCategory).where(WebCategory.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名已存在")

    category = WebCategory(**payload.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=WebCategoryPublic)
def update_category(
    category_id: int,
    payload: WebCategoryCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """更新分类（仅管理员）。"""
    category = session.get(WebCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查新名称是否与其他分类冲突
    if payload.name != category.name:
        existing = session.exec(
            select(WebCategory).where(WebCategory.name == payload.name)
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
    _: User = Depends(require_admin),
):
    """删除分类（仅管理员）。"""
    category = session.get(WebCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查是否有关联的页面
    pages = session.exec(
        select(WebPage).where(WebPage.category_id == category_id)
    ).all()
    if pages:
        raise HTTPException(
            status_code=400,
            detail=f"该分类下还有 {len(pages)} 个页面，请先删除这些页面"
        )

    session.delete(category)
    session.commit()
    return None


# ==================== 页面管理 ====================

@router.get("/pages", response_model=list[WebPagePublic])
def list_pages(
    category_id: Optional[int] = Query(None, description="按分类 ID 筛选"),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """获取页面列表，可选按分类筛选。"""
    query = select(WebPage)
    if category_id is not None:
        query = query.where(WebPage.category_id == category_id)
    
    pages = session.exec(query).all()
    return pages


@router.post("/pages", response_model=WebPagePublic, status_code=status.HTTP_201_CREATED)
def create_page(
    payload: WebPageCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """创建新页面（仅管理员）。"""
    # 验证分类是否存在
    category = session.get(WebCategory, payload.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="分类不存在")

    page = WebPage(**payload.model_dump())
    session.add(page)
    session.commit()
    session.refresh(page)
    return page


@router.put("/pages/{page_id}", response_model=WebPagePublic)
def update_page(
    page_id: int,
    payload: WebPageCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """更新页面（仅管理员）。"""
    page = session.get(WebPage, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    # 如果更改了分类，验证新分类是否存在
    if payload.category_id != page.category_id:
        category = session.get(WebCategory, payload.category_id)
        if not category:
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
    _: User = Depends(require_admin),
):
    """删除页面（仅管理员）。"""
    page = session.get(WebPage, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    session.delete(page)
    session.commit()
    return None
