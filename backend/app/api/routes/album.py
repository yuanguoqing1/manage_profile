import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.album import Album, AlbumCreate, AlbumRead, Photo, PhotoCreate, PhotoRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/albums", response_model=List[AlbumRead])
def get_albums(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有相册"""
    statement = select(Album).where(Album.user_id == current_user.id).order_by(Album.created_at.desc())
    return session.exec(statement).all()


@router.post("/albums", response_model=AlbumRead)
def create_album(
    album_in: AlbumCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """创建新相册"""
    album = Album(**album_in.dict(), user_id=current_user.id)
    session.add(album)
    session.commit()
    session.refresh(album)
    return album


@router.delete("/albums/{album_id}")
def delete_album(
    album_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除相册及其所有照片"""
    album = session.get(Album, album_id)
    if not album or album.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    # 删除相册中的所有照片
    photos = session.exec(select(Photo).where(Photo.album_id == album_id)).all()
    for photo in photos:
        session.delete(photo)
    
    session.delete(album)
    session.commit()
    return {"message": "相册已删除"}


@router.get("/albums/{album_id}/photos", response_model=List[PhotoRead])
def get_photos(
    album_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取相册中的所有照片"""
    album = session.get(Album, album_id)
    if not album or album.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    statement = select(Photo).where(Photo.album_id == album_id).order_by(Photo.created_at.desc())
    return session.exec(statement).all()


@router.post("/photos/upload")
async def upload_photo(
    album_id: int = Form(...),
    caption: str = Form(default=""),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """上传照片到相册"""
    album = session.get(Album, album_id)
    if not album or album.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、GIF、WEBP 格式")
    
    # 生成唯一文件名
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # 创建照片记录
    photo = Photo(
        url=f"/uploads/{filename}",
        caption=caption,
        album_id=album_id,
        user_id=current_user.id,
    )
    session.add(photo)
    
    # 如果相册没有封面，设置第一张照片为封面
    if not album.cover_url:
        album.cover_url = photo.url
        session.add(album)
    
    session.commit()
    session.refresh(photo)
    
    return {"id": photo.id, "url": photo.url, "caption": photo.caption}


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """删除照片"""
    photo = session.get(Photo, photo_id)
    if not photo or photo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    session.delete(photo)
    session.commit()
    return {"message": "照片已删除"}
