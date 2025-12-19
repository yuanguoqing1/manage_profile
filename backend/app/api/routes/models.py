"""模型配置路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import ModelConfig, User
from app.schemas.user import ModelConfigCreate, ModelConfigPublic, ModelConfigUpdate

router = APIRouter(prefix="/models", tags=["models"])


def _get_model_or_404(session: Session, model_id: int) -> ModelConfig:
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return model


@router.get("", response_model=list[ModelConfigPublic])
def list_models(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if user.role == "admin":
        return session.exec(select(ModelConfig)).all()
    return session.exec(
        select(ModelConfig).where((ModelConfig.owner_id.is_(None)) | (ModelConfig.owner_id == user.id))
    ).all()


@router.post("", response_model=ModelConfigPublic, status_code=status.HTTP_201_CREATED)
def create_model(
    payload: ModelConfigCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    if payload.owner_id is not None and not session.get(User, payload.owner_id):
        raise HTTPException(status_code=400, detail="用户不存在")

    model = ModelConfig(**payload.model_dump())
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.put("/{model_id}", response_model=ModelConfigPublic)
def update_model(
    model_id: int,
    payload: ModelConfigUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    model = _get_model_or_404(session, model_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "owner_id" in update_data and update_data["owner_id"] is not None:
        if not session.get(User, update_data["owner_id"]):
            raise HTTPException(status_code=400, detail="用户不存在")

    for key, value in update_data.items():
        setattr(model, key, value)
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    model = _get_model_or_404(session, model_id)
    session.delete(model)
    session.commit()
    return None
