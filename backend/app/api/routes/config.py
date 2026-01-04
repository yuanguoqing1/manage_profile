"""系统配置路由。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import require_admin
from app.db.session import get_session
from app.models.user import SystemConfig, User
from app.schemas.user import SystemConfigCreate, SystemConfigPublic, SystemConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])

# 预定义的配置项
DEFAULT_CONFIGS = [
    {"key": "AMAP_KEY", "description": "高德地图 API Key"},
    {"key": "OPENAI_API_KEY", "description": "OpenAI API Key"},
    {"key": "OPENAI_BASE_URL", "description": "OpenAI API 地址"},
]


@router.get("", response_model=list[SystemConfigPublic])
def list_configs(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """获取所有配置（仅管理员）。"""
    configs = session.exec(select(SystemConfig)).all()
    
    # 确保预定义的配置项存在
    existing_keys = {c.key for c in configs}
    for default in DEFAULT_CONFIGS:
        if default["key"] not in existing_keys:
            new_config = SystemConfig(
                key=default["key"],
                value="",
                description=default["description"],
                updated_at=datetime.now().isoformat(),
            )
            session.add(new_config)
            configs.append(new_config)
    
    session.commit()
    return configs


@router.get("/{key}")
def get_config(
    key: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """获取单个配置（仅管理员）。"""
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.post("", response_model=SystemConfigPublic, status_code=status.HTTP_201_CREATED)
def create_config(
    payload: SystemConfigCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """创建配置（仅管理员）。"""
    existing = session.exec(select(SystemConfig).where(SystemConfig.key == payload.key)).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置已存在")
    
    config = SystemConfig(
        key=payload.key,
        value=payload.value,
        description=payload.description,
        updated_at=datetime.now().isoformat(),
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@router.put("/{key}", response_model=SystemConfigPublic)
def update_config(
    key: str,
    payload: SystemConfigUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """更新配置（仅管理员）。"""
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config:
        # 如果不存在，创建新的
        config = SystemConfig(
            key=key,
            value=payload.value or "",
            description=payload.description,
            updated_at=datetime.now().isoformat(),
        )
        session.add(config)
    else:
        if payload.value is not None:
            config.value = payload.value
        if payload.description is not None:
            config.description = payload.description
        config.updated_at = datetime.now().isoformat()
    
    session.commit()
    session.refresh(config)
    return config


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    key: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """删除配置（仅管理员）。"""
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    session.delete(config)
    session.commit()
    return None


# 公开接口：获取前端需要的配置（不需要登录）
@router.get("/public/{key}")
def get_public_config(
    key: str,
    session: Session = Depends(get_session),
):
    """获取公开配置（如高德地图Key）。"""
    # 只允许获取特定的公开配置
    allowed_keys = ["AMAP_KEY"]
    if key not in allowed_keys:
        raise HTTPException(status_code=403, detail="无权访问此配置")
    
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config or not config.value:
        return {"key": key, "value": ""}
    return {"key": key, "value": config.value}
