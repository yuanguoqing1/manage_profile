from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class AlbumBase(SQLModel):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)


class Album(AlbumBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    cover_url: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlbumCreate(AlbumBase):
    pass


class AlbumRead(AlbumBase):
    id: int
    user_id: int
    cover_url: str
    created_at: datetime


class PhotoBase(SQLModel):
    url: str = Field(max_length=500)
    caption: str = Field(default="", max_length=200)


class Photo(PhotoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    album_id: int = Field(foreign_key="album.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PhotoCreate(PhotoBase):
    album_id: int


class PhotoRead(PhotoBase):
    id: int
    album_id: int
    user_id: int
    created_at: datetime
