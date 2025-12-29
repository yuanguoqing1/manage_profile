"""基础 CRUD 操作，支持软删除。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, Type, TypeVar

from sqlmodel import Session, SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


def utc_now() -> datetime:
    """获取当前 UTC 时间（带时区信息）。"""
    return datetime.now(timezone.utc)


class CRUDBase(Generic[ModelType]):
    """基础 CRUD 类，支持软删除。"""

    def __init__(self, model: Type[ModelType]):
        """初始化 CRUD 对象。
        
        Args:
            model: SQLModel 模型类
        """
        self.model = model

    def get(self, session: Session, id: int, include_deleted: bool = False) -> ModelType | None:
        """根据 ID 获取记录。
        
        Args:
            session: 数据库会话
            id: 记录 ID
            include_deleted: 是否包含已删除的记录
        
        Returns:
            模型实例或 None
        """
        obj = session.get(self.model, id)
        if obj and not include_deleted and hasattr(obj, "deleted_at") and obj.deleted_at:
            return None
        return obj

    def get_multi(
        self, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False
    ) -> list[ModelType]:
        """获取多条记录。
        
        Args:
            session: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_deleted: 是否包含已删除的记录
        
        Returns:
            模型实例列表
        """
        query = select(self.model).offset(skip).limit(limit)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        return session.exec(query).all()

    def create(self, session: Session, obj_in: dict) -> ModelType:
        """创建记录。
        
        Args:
            session: 数据库会话
            obj_in: 输入数据字典
        
        Returns:
            创建的模型实例
        """
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(self, session: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        """更新记录。
        
        Args:
            session: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据字典
        
        Returns:
            更新后的模型实例
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        
        if hasattr(db_obj, "updated_at"):
            db_obj.updated_at = utc_now()
        
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def soft_delete(self, session: Session, id: int) -> ModelType | None:
        """软删除记录。
        
        Args:
            session: 数据库会话
            id: 记录 ID
        
        Returns:
            删除的模型实例或 None
        """
        obj = self.get(session, id)
        if not obj:
            return None
        
        if hasattr(obj, "deleted_at"):
            obj.deleted_at = utc_now()
            session.add(obj)
            session.commit()
            session.refresh(obj)
        
        return obj

    def hard_delete(self, session: Session, id: int) -> bool:
        """硬删除记录（物理删除）。
        
        Args:
            session: 数据库会话
            id: 记录 ID
        
        Returns:
            是否删除成功
        """
        obj = session.get(self.model, id)
        if not obj:
            return False
        
        session.delete(obj)
        session.commit()
        return True

    def restore(self, session: Session, id: int) -> ModelType | None:
        """恢复软删除的记录。
        
        Args:
            session: 数据库会话
            id: 记录 ID
        
        Returns:
            恢复的模型实例或 None
        """
        obj = self.get(session, id, include_deleted=True)
        if not obj or not hasattr(obj, "deleted_at") or not obj.deleted_at:
            return None
        
        obj.deleted_at = None
        if hasattr(obj, "updated_at"):
            obj.updated_at = utc_now()
        
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
