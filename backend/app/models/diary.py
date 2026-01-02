from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class DiaryBase(SQLModel):
    title: str = Field(default="", max_length=200)
    content: str = Field(default="")
    mood: str = Field(default="😊", max_length=10)


class Diary(DiaryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DiaryCreate(DiaryBase):
    pass


class DiaryUpdate(DiaryBase):
    pass


class DiaryRead(DiaryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
