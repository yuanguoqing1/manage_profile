"""管理员路由：用户管理、角色统计。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.api.deps import get_current_user, require_admin
from app.core.security import generate_salt, hash_password
from app.crud.user import create_user, get_user_by_name
from app.db.session import get_session
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserPublic, UserUpdate

router = APIRouter(tags=["admin"])


@router.get("/users", response_model=list[UserPublic])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """获取所有用户列表（仅管理员）。"""
    users = session.exec(select(User)).all()
    return [
        UserPublic(
            id=u.id,
            name=u.name,
            balance=u.balance,
            role=u.role,
            email=u.email,
            phone=u.phone,
            LDC=u.LDC or 0,
            last_check_in=u.last_check_in,
        )
        for u in users
    ]


@router.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    payload: UserCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """创建新用户（仅管理员）。"""
    if not payload.password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")

    existing = get_user_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    chosen_role = payload.role.value if payload.role else Role.user.value
    salt = generate_salt()
    password_hash = hash_password(payload.password, salt)
    user = create_user(session, payload, chosen_role, password_hash, salt)

    return UserPublic(
        id=user.id,
        name=user.name,
        balance=user.balance,
        role=user.role,
        email=user.email,
        phone=user.phone,
        LDC=user.LDC or 0,
        last_check_in=user.last_check_in,
    )


@router.put("/users/{user_id}", response_model=UserPublic)
def update_user_admin(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """更新用户信息（仅管理员）。"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = payload.model_dump(exclude_unset=True)
    
    # 如果更新密码，需要重新哈希
    if "password" in update_data and update_data["password"]:
        salt = generate_salt()
        update_data["password_hash"] = hash_password(update_data["password"], salt)
        update_data["salt"] = salt
        del update_data["password"]

    for key, value in update_data.items():
        setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserPublic(
        id=user.id,
        name=user.name,
        balance=user.balance,
        role=user.role,
        email=user.email,
        phone=user.phone,
        LDC=user.LDC or 0,
        last_check_in=user.last_check_in,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_admin(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """删除用户（仅管理员）。"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    session.delete(user)
    session.commit()
    return None


@router.get("/roles")
def get_role_stats(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """获取角色统计（仅管理员）。"""
    admin_count = session.exec(
        select(func.count()).select_from(User).where(User.role == Role.admin.value)
    ).one()
    user_count = session.exec(
        select(func.count()).select_from(User).where(User.role == Role.user.value)
    ).one()
    
    return {
        "roles": {
            "admin": admin_count,
            "user": user_count,
        }
    }
