"""模型包入口。"""

from app.models.album import Album, Photo
from app.models.diary import Diary
from app.models.message import PeerMessage
from app.models.token import AuthToken
from app.models.user import ModelConfig, Role, RolePrompt, User, WebCategory, WebPage

__all__ = [
    "Album",
    "AuthToken",
    "Diary",
    "ModelConfig",
    "PeerMessage",
    "Photo",
    "Role",
    "RolePrompt",
    "User",
    "WebCategory",
    "WebPage",
]
