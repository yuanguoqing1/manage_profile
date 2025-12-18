from __future__ import annotations

import datetime as dt
import hashlib
import logging
import os
import secrets
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Union, Set

import httpx

try:
    import redis
except ImportError:  # pragma: no cover - 在无依赖环境下自动降级
    redis = None  # type: ignore

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from datetime import datetime

from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, or_
from sqlmodel import Field, Session, SQLModel, create_engine, select


LOG_FILE = Path("app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
)


class Role(str, Enum):
    """角色类型"""

    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    """用户表"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0, ge=0.0)
    password_hash: str
    salt: str
    role: str = Field(default=Role.user.value, index=True)


class UserCreate(SQLModel):
    """注册/创建用户入参"""

    name: str
    password: str
    role: Optional[Role] = None


class UserPublic(SQLModel):
    """对外展示的用户信息"""

    id: int
    name: str
    balance: float
    role: str


class UserContactPublic(SQLModel):
    """站内互聊展示的联系人信息"""

    id: int
    name: str
    role: str


class UserContactStatusPublic(UserContactPublic):
    """带在线状态的联系人信息"""

    is_online: bool


class BalanceUpdate(SQLModel):
    """余额调整入参"""

    amount: float


class ModelConfig(SQLModel, table=True):
    """大模型配置表"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")


class ModelConfigCreate(SQLModel):
    name: str
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 1.0
    owner_id: Optional[int] = None


class ModelConfigPublic(SQLModel):
    id: int
    name: str
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int
    temperature: float
    owner_id: Optional[int]


class WebCategory(SQLModel, table=True):
    """网页分类"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")


class WebPage(SQLModel, table=True):
    """网页信息记录"""

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="webcategory.id")
    url: str
    account: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    cookie: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)


class WebCategoryCreate(SQLModel):
    name: str
    description: str = ""


class WebCategoryPublic(SQLModel):
    id: int
    name: str
    description: str


class WebPageCreate(SQLModel):
    category_id: int
    url: str
    account: Optional[str] = None
    password: Optional[str] = None
    cookie: Optional[str] = None
    note: Optional[str] = None


class WebPagePublic(SQLModel):
    id: int
    category_id: int
    url: str
    account: Optional[str]
    password: Optional[str]
    cookie: Optional[str]
    note: Optional[str]


class LoginRequest(SQLModel):
    """登录入参"""

    name: str
    password: str


class LoginResponse(SQLModel):
    token: str
    user: UserPublic


class ChatMessage(SQLModel):
    """聊天消息"""

    role: str
    content: str


class PeerMessage(SQLModel, table=True):
    """站内互聊消息表"""

    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatCompletionRequest(SQLModel):
    """聊天请求参数"""

    model_id: Optional[int] = None
    messages: List[ChatMessage]
    stream: bool = False
    role_prompt: Optional[str] = None
    role_id: Optional[int] = None


UsageValue = Union[int, Dict[str, int]]


class ChatCompletionResponse(SQLModel):
    """与 OpenAI 对齐的返回体"""

    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, object]]
    usage: Dict[str, UsageValue]


class PeerMessageCreate(SQLModel):
    """创建站内互聊消息入参"""

    receiver_id: int
    content: str


class PeerMessagePublic(SQLModel):
    """站内互聊返回体"""

    id: int
    sender_id: int
    receiver_id: int
    sender_name: str
    receiver_name: str
    content: str
    created_at: datetime


class UserUpdate(SQLModel):
    """用户信息更新入参"""

    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Role] = None


class ModelConfigUpdate(SQLModel):
    """大模型配置更新入参"""

    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    owner_id: Optional[int] = None


class RolePrompt(SQLModel, table=True):
    """提示词角色表"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    prompt: str


class RolePromptCreate(SQLModel):
    """新增提示词入参"""

    name: str
    prompt: str


class RolePromptUpdate(SQLModel):
    """更新提示词入参"""

    name: Optional[str] = None
    prompt: Optional[str] = None


class RolePromptPublic(SQLModel):
    id: int
    name: str
    prompt: str


class RoleUpdate(SQLModel):
    """角色赋予入参"""

    user_id: int
    role: Role


class JobAutomationConfig(SQLModel, table=True):
    """get_jobs 服务集成配置"""

    id: Optional[int] = Field(default=1, primary_key=True)
    service_url: str = Field(default="", description="get_jobs 服务接收任务的地址")
    service_token: Optional[str] = Field(default=None, description="get_jobs 服务鉴权 token，可选")
    resume_link: Optional[str] = Field(default=None, description="简历链接或存储地址")
    greeting: str = Field(
        default="您好，我对岗位很感兴趣，这是我的简历，期待沟通。",
        description="开场白模板",
    )
    keywords: str = Field(default="", description="投递关键词，逗号分隔")
    cities: str = Field(default="", description="城市列表，逗号分隔")
    auto_apply: bool = Field(default=True, description="是否自动投递")
    auto_greet: bool = Field(default=True, description="是否自动打招呼")
    daily_limit: int = Field(default=30, description="每日最大投递数量")


class JobAutomationConfigPublic(SQLModel):
    id: int
    service_url: str
    service_token: Optional[str]
    resume_link: Optional[str]
    greeting: str
    keywords: str
    cities: str
    auto_apply: bool
    auto_greet: bool
    daily_limit: int


class JobAutomationConfigUpdate(SQLModel):
    service_url: Optional[str] = None
    service_token: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    keywords: Optional[str] = None
    cities: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None


class JobRun(SQLModel, table=True):
    """投递任务执行记录"""

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="pending")
    message: str = Field(default="")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    requested_by: int
    keywords: Optional[str] = None
    cities: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None


class JobRunPublic(SQLModel):
    id: int
    status: str
    message: str
    requested_at: datetime
    finished_at: Optional[datetime]
    requested_by: int
    keywords: Optional[str]
    cities: Optional[str]
    resume_link: Optional[str]
    greeting: Optional[str]
    auto_apply: Optional[bool]
    auto_greet: Optional[bool]
    daily_limit: Optional[int]


class JobRunRequest(SQLModel):
    keywords: Optional[str] = None
    cities: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None


sqlite_url = "sqlite:///./data.db"
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

# 注意：内存态 token_store，多 worker 会失效（必须单进程/单 worker）
token_store: Dict[str, Dict[str, int]] = {}


def ensure_columns() -> None:
    """确保旧表拥有新字段，缺失时自动补齐。"""

    required_columns = {
        "user": {
            "password_hash": "TEXT",
            "salt": "TEXT",
            "role": "TEXT DEFAULT 'user'",
        }
    }
    with engine.begin() as conn:
        for table, columns in required_columns.items():
            existing = {row[1] for row in conn.exec_driver_sql(f'PRAGMA table_info("{table}")').all()}
            for column, sql_type in columns.items():
                if column not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")  # noqa: S608


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    ensure_columns()


def get_session():
    with Session(engine) as session:
        yield session


def init_redis() -> Optional["redis.Redis"]:
    """初始化 Redis 客户端，失败时返回 None。"""

    if redis is None:
        return None
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    password = os.getenv("REDIS_PASSWORD")
    try:
        client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        print(f"Redis 不可用，使用内存计数，原因：{exc}")
        return None


redis_client = init_redis()
fallback_counters: Dict[str, set | int] = {"register": 0, "online_tokens": set()}


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def admin_exists(session: Session) -> bool:
    return session.exec(select(User).where(User.role == Role.admin.value)).first() is not None


def increment_register_count() -> None:
    if redis_client:
        redis_client.incr("register_count")
    else:
        fallback_counters["register"] = int(fallback_counters["register"]) + 1


def register_user_online(token: str) -> None:
    if redis_client:
        redis_client.sadd("online_tokens", token)
    else:
        fallback_counters["online_tokens"].add(token)


def logout_user_online(token: str) -> None:
    if redis_client:
        redis_client.srem("online_tokens", token)
    else:
        fallback_counters["online_tokens"].discard(token)


def get_online_count() -> int:
    if redis_client:
        return redis_client.scard("online_tokens")
    return len(fallback_counters["online_tokens"])


def get_register_count() -> int:
    if redis_client:
        value = redis_client.get("register_count")
        return int(value) if value else 0
    return int(fallback_counters["register"])


# -----------------------------
# WebSocket 连接管理（新增）
# -----------------------------
class ConnectionManager:
    """管理用户 WebSocket 连接（同一用户允许多个连接，例如多标签页）。"""

    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, set()).add(ws)
        logging.info("WS connect user_id=%s connections=%s", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
        logging.info("WS disconnect user_id=%s remain=%s", user_id, len(self._connections.get(user_id, [])))

    async def send_to(self, user_id: int, payload: dict) -> None:
        conns = list(self._connections.get(user_id, set()))
        if not conns:
            return
        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    def is_ws_online(self, user_id: int) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0


ws_manager = ConnectionManager()


def _get_allowed_origins() -> List[str]:
    env_value = os.getenv("ALLOWED_ORIGINS", "")
    if env_value:
        return [origin.strip() for origin in env_value.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.30.79.140:5173",
    ]


app = FastAPI(title="Profile Manager", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


def get_current_user(
    authorization: str = Header(default=None), session: Session = Depends(get_session)
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少凭证")
    token = authorization.split()[1]
    record = token_store.get(token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    user = session.get(User, record["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_user_by_token(token: str, session: Session) -> User:
    record = token_store.get(token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    user = session.get(User, record["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def get_job_config(session: Session) -> JobAutomationConfig:
    config = session.get(JobAutomationConfig, 1)
    if config:
        return config
    config = JobAutomationConfig()
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def merge_job_config(config: JobAutomationConfig, payload: JobRunRequest) -> JobRunRequest:
    return JobRunRequest(
        keywords=payload.keywords if payload.keywords is not None else config.keywords,
        cities=payload.cities if payload.cities is not None else config.cities,
        resume_link=payload.resume_link if payload.resume_link is not None else config.resume_link,
        greeting=payload.greeting if payload.greeting is not None else config.greeting,
        auto_apply=payload.auto_apply if payload.auto_apply is not None else config.auto_apply,
        auto_greet=payload.auto_greet if payload.auto_greet is not None else config.auto_greet,
        daily_limit=payload.daily_limit if payload.daily_limit is not None else config.daily_limit,
    )


def call_get_jobs(
    *,
    config: JobAutomationConfig,
    merged: JobRunRequest,
) -> str:
    if not config.service_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先配置 get_jobs 服务地址")

    headers = {"Content-Type": "application/json"}
    if config.service_token:
        headers["Authorization"] = f"Bearer {config.service_token}"

    payload = {
        "keywords": merged.keywords,
        "cities": merged.cities,
        "resume_link": merged.resume_link,
        "greeting": merged.greeting,
        "auto_apply": merged.auto_apply,
        "auto_greet": merged.auto_greet,
        "daily_limit": merged.daily_limit,
    }

    try:
        response = httpx.post(config.service_url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - 外部服务不易模拟
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"get_jobs 调用失败：{exc}") from exc

    return response.text[:500]


# -----------------------------
# WebSocket 路由（新增）
# -----------------------------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        # 兼容部分客户端无法携带查询参数时的头部传递
        auth_header = ws.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split()[1]

    if not token:
        await ws.accept()
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="缺少 token")
        return

    with Session(engine) as session:
        try:
            user = get_user_by_token(token, session)
        except HTTPException as exc:
            await ws.accept()
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=exc.detail)
            return

        await ws_manager.connect(user.id, ws)
        try:
            while True:
                # 客户端可以发 ping 文本，服务端只保持连接即可
                await ws.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(user.id, ws)
        except Exception:  # noqa: BLE001
            ws_manager.disconnect(user.id, ws)
            try:
                await ws.close(code=1011)
            except Exception:  # noqa: BLE001
                pass


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, session: Session = Depends(get_session)):
    if not payload.password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")
    existing = session.exec(select(User).where(User.name == payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    chosen_role = Role.user.value
    if payload.role:
        if payload.role == Role.admin and not admin_exists(session):
            chosen_role = payload.role.value
        elif payload.role == Role.user:
            chosen_role = payload.role.value

    salt = secrets.token_hex(8)
    password_hash = hash_password(payload.password, salt)
    user = User(name=payload.name, balance=0.0, password_hash=password_hash, salt=salt, role=chosen_role)
    session.add(user)
    session.commit()
    session.refresh(user)
    increment_register_count()
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.name == payload.name)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    hashed = hash_password(payload.password, user.salt)
    if hashed != user.password_hash:
        raise HTTPException(status_code=401, detail="密码错误")
    token = secrets.token_urlsafe(24)
    token_store[token] = {"user_id": user.id}
    register_user_online(token)
    public_user = UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)
    return LoginResponse(token=token, user=public_user)


@app.post("/auth/logout")
def logout(authorization: str = Header(default=None), user: User = Depends(get_current_user)):
    token = authorization.split()[1]
    token_store.pop(token, None)
    logout_user_online(token)
    return {"message": f"{user.name} 已退出"}


@app.get("/auth/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)):
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    if not user_in.password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")
    existing = session.exec(select(User).where(User.name == user_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    role_value = user_in.role.value if user_in.role else Role.user.value
    salt = secrets.token_hex(8)
    password_hash = hash_password(user_in.password, salt)
    user = User(name=user_in.name, balance=0.0, password_hash=password_hash, salt=salt, role=role_value)
    session.add(user)
    session.commit()
    session.refresh(user)
    increment_register_count()
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.get("/users", response_model=List[UserPublic])
def list_users(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    return [UserPublic(id=u.id, name=u.name, balance=u.balance, role=u.role) for u in users]


@app.get("/contacts", response_model=List[UserContactStatusPublic])
def list_contacts(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """获取站内互聊联系人列表，排除当前用户。
    在线状态：token_store（登录态） + ws 连接（更实时）
    """
    online_user_ids = {info.get("user_id") for info in token_store.values() if info.get("user_id")}
    contacts = session.exec(select(User).where(User.id != user.id)).all()
    return [
        UserContactStatusPublic(
            id=item.id,
            name=item.name,
            role=item.role,
            is_online=(item.id in online_user_ids) or ws_manager.is_ws_online(item.id),
        )
        for item in contacts
    ]


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.name and payload.name != user.name:
        exists = session.exec(select(User).where(User.name == payload.name)).first()
        if exists:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.name = payload.name

    if payload.password is not None:
        if not payload.password.strip():
            raise HTTPException(status_code=400, detail="密码不能为空")
        user.salt = secrets.token_hex(8)
        user.password_hash = hash_password(payload.password, user.salt)

    if payload.role:
        user.role = payload.role.value

    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    logging.info("删除用户：%s", user.name)
    return None


@app.get("/contacts/messages/{peer_id}", response_model=List[PeerMessagePublic])
def get_peer_messages(peer_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    peer = session.get(User, peer_id)
    if not peer:
        raise HTTPException(status_code=404, detail="联系人不存在")

    query = (
        select(PeerMessage)
        .where(
            or_(
                and_(PeerMessage.sender_id == user.id, PeerMessage.receiver_id == peer_id),
                and_(PeerMessage.sender_id == peer_id, PeerMessage.receiver_id == user.id),
            )
        )
        .order_by(PeerMessage.created_at)
    )
    messages = session.exec(query).all()
    return [
        PeerMessagePublic(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            sender_name=peer.name if msg.sender_id == peer.id else user.name,
            receiver_name=peer.name if msg.receiver_id == peer.id else user.name,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


# 改为 async：落库后 WS 推送（关键）
@app.post("/contacts/messages", response_model=PeerMessagePublic, status_code=status.HTTP_201_CREATED)
async def create_peer_message(
    payload: PeerMessageCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    if payload.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发送消息")

    receiver = session.get(User, payload.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="联系人不存在")

    message = PeerMessage(sender_id=user.id, receiver_id=payload.receiver_id, content=content)
    session.add(message)
    session.commit()
    session.refresh(message)

    public_msg = PeerMessagePublic(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        sender_name=user.name,
        receiver_name=receiver.name,
        content=message.content,
        created_at=message.created_at,
    )

    payload_ws = {"type": "peer_message", "data": public_msg.model_dump()}

    # 推送给接收方（实时收到）
    await ws_manager.send_to(receiver.id, payload_ws)
    # 也推给发送方（其他标签页/设备同步显示）
    await ws_manager.send_to(user.id, payload_ws)

    return public_msg


@app.put("/users/{user_id}/balance", response_model=UserPublic)
def update_balance(user_id: int, update: BalanceUpdate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_balance = user.balance + update.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Balance cannot be negative")
    user.balance = new_balance
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.post("/models", response_model=ModelConfigPublic, status_code=status.HTTP_201_CREATED)
def create_model_config(key: ModelConfigCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    existing = session.exec(select(ModelConfig).where(ModelConfig.name == key.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="模型配置名称已存在")
    if key.owner_id and not session.get(User, key.owner_id):
        raise HTTPException(status_code=404, detail="绑定用户不存在")
    model = ModelConfig(
        name=key.name,
        base_url=key.base_url,
        api_key=key.api_key,
        model_name=key.model_name,
        max_tokens=key.max_tokens,
        temperature=key.temperature,
        owner_id=key.owner_id,
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    logging.info("新增大模型配置：%s", model.name)
    return ModelConfigPublic(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        api_key=model.api_key,
        model_name=model.model_name,
        max_tokens=model.max_tokens,
        temperature=model.temperature,
        owner_id=model.owner_id,
    )


@app.get("/models", response_model=List[ModelConfigPublic])
def list_models(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    models = session.exec(select(ModelConfig)).all()
    return [
        ModelConfigPublic(
            id=m.id,
            name=m.name,
            base_url=m.base_url,
            api_key=m.api_key,
            model_name=m.model_name,
            max_tokens=m.max_tokens,
            temperature=m.temperature,
            owner_id=m.owner_id,
        )
        for m in models
    ]


@app.get("/models/{model_id}", response_model=ModelConfigPublic)
def get_model_config(model_id: int, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return ModelConfigPublic(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        api_key=model.api_key,
        model_name=model.model_name,
        max_tokens=model.max_tokens,
        temperature=model.temperature,
        owner_id=model.owner_id,
    )


@app.put("/models/{model_id}", response_model=ModelConfigPublic)
def update_model_config(model_id: int, payload: ModelConfigUpdate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    if payload.name and payload.name != model.name:
        existing = session.exec(select(ModelConfig).where(ModelConfig.name == payload.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail="模型配置名称已存在")
        model.name = payload.name

    if payload.owner_id and not session.get(User, payload.owner_id):
        raise HTTPException(status_code=404, detail="绑定用户不存在")

    if payload.base_url is not None:
        model.base_url = payload.base_url
    if payload.api_key is not None:
        model.api_key = payload.api_key
    if payload.model_name is not None:
        model.model_name = payload.model_name
    if payload.max_tokens is not None:
        model.max_tokens = payload.max_tokens
    if payload.temperature is not None:
        model.temperature = payload.temperature
    if payload.owner_id is not None:
        model.owner_id = payload.owner_id

    session.add(model)
    session.commit()
    session.refresh(model)
    logging.info("更新大模型配置：%s", model.name)
    return ModelConfigPublic(
        id=model.id,
        name=model.name,
        base_url=model.base_url,
        api_key=model.api_key,
        model_name=model.model_name,
        max_tokens=model.max_tokens,
        temperature=model.temperature,
        owner_id=model.owner_id,
    )


@app.delete("/models/{model_id}", status_code=204)
def delete_model_config(model_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    session.delete(model)
    session.commit()
    logging.info("删除大模型配置：%s", model.name)
    return None


@app.post("/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(payload: ChatCompletionRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    model: Optional[ModelConfig] = None
    if payload.model_id:
        model = session.get(ModelConfig, payload.model_id)
    if not model:
        model = session.exec(select(ModelConfig)).first()
    if not model:
        raise HTTPException(status_code=404, detail="尚未配置可用模型")
    if model.owner_id and user.role != Role.admin.value and user.id != model.owner_id:
        raise HTTPException(status_code=403, detail="无权使用该模型")

    target_url = f"{model.base_url.rstrip('/')}/v1/chat/completions"
    system_prompts = [
        {
            "role": "system",
            "content": f"当前用户昵称：{user.name}，角色：{user.role}。请在回答时体现礼貌、简洁并结合用户身份。",
        }
    ]

    role_prompt_text = payload.role_prompt
    if payload.role_id:
        prompt_record = session.get(RolePrompt, payload.role_id)
        if not prompt_record:
            raise HTTPException(status_code=404, detail="提示词不存在")
        role_prompt_text = prompt_record.prompt
    if not role_prompt_text:
        fallback_prompt = session.exec(select(RolePrompt).order_by(RolePrompt.id)).first()
        if fallback_prompt:
            role_prompt_text = fallback_prompt.prompt

    if role_prompt_text:
        system_prompts.append({"role": "system", "content": role_prompt_text})

    merged_messages = [*system_prompts, *[msg.model_dump() for msg in payload.messages]]
    request_body = {
        "model": model.model_name,
        "messages": merged_messages,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
    }
    if payload.stream:
        request_body["stream"] = True

    if payload.stream:

        def stream_response():
            try:
                with httpx.Client(timeout=30.0) as client:
                    with client.stream(
                        "POST",
                        target_url,
                        headers={"Authorization": f"Bearer {model.api_key}"},
                        json=request_body,
                    ) as upstream_response:
                        if upstream_response.status_code >= 400:
                            # 主动读取完整响应，避免 httpx 在流模式下抛出 ResponseNotRead
                            error_bytes = upstream_response.read()
                            error_text = error_bytes.decode("utf-8", errors="replace")
                            try:
                                error_body = upstream_response.json()
                                error_text = error_body.get("error", {}).get("message", error_text)
                            except ValueError:
                                pass
                            raise HTTPException(
                                status_code=upstream_response.status_code,
                                detail=f"上游错误：{error_text}",
                            )
                        for chunk in upstream_response.iter_text():
                            if chunk:
                                yield chunk
            except httpx.RequestError as exc:  # pragma: no cover
                raise HTTPException(status_code=502, detail=f"请求上游模型失败：{exc}") from exc

        return StreamingResponse(stream_response(), media_type="text/event-stream")

    try:
        with httpx.Client(timeout=30.0) as client:
            upstream_response = client.post(
                target_url,
                headers={"Authorization": f"Bearer {model.api_key}"},
                json=request_body,
            )
    except httpx.RequestError as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"请求上游模型失败：{exc}") from exc

    if upstream_response.status_code >= 400:
        try:
            error_body = upstream_response.json()
            error_message = error_body.get("error", {}).get("message", upstream_response.text)
        except ValueError:
            error_message = upstream_response.text
        raise HTTPException(status_code=upstream_response.status_code, detail=f"上游错误：{error_message}")

    data = upstream_response.json()
    now_ts = int(dt.datetime.now().timestamp())
    data.setdefault("id", f"chatcmpl-{secrets.token_hex(6)}")
    data.setdefault("object", "chat.completion")
    data.setdefault("created", now_ts)
    data.setdefault("model", model.model_name)
    data.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    return data


@app.post("/web/categories", response_model=WebCategoryPublic, status_code=status.HTTP_201_CREATED)
def create_web_category(payload: WebCategoryCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    existing = session.exec(select(WebCategory).where(WebCategory.name == payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    category = WebCategory(name=payload.name, description=payload.description)
    session.add(category)
    session.commit()
    session.refresh(category)
    logging.info("新增网页分类：%s", category.name)
    return WebCategoryPublic(id=category.id, name=category.name, description=category.description)


@app.get("/web/categories", response_model=List[WebCategoryPublic])
def list_web_categories(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    categories = session.exec(select(WebCategory)).all()
    return [WebCategoryPublic(id=c.id, name=c.name, description=c.description) for c in categories]


@app.delete("/web/categories/{category_id}", status_code=204)
def delete_web_category(category_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    category = session.get(WebCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    pages = session.exec(select(WebPage).where(WebPage.category_id == category_id)).all()
    for page in pages:
        session.delete(page)
    session.delete(category)
    session.commit()
    logging.info("删除网页分类：%s", category.name)
    return None


@app.post("/web/pages", response_model=WebPagePublic, status_code=status.HTTP_201_CREATED)
def create_web_page(payload: WebPageCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    category = session.get(WebCategory, payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    page = WebPage(
        category_id=payload.category_id,
        url=payload.url,
        account=payload.account,
        password=payload.password,
        cookie=payload.cookie,
        note=payload.note,
    )
    session.add(page)
    session.commit()
    session.refresh(page)
    logging.info("分类 %s 新增网页：%s", category.name, page.url)
    return WebPagePublic(
        id=page.id,
        category_id=page.category_id,
        url=page.url,
        account=page.account,
        password=page.password,
        cookie=page.cookie,
        note=page.note,
    )


@app.get("/web/pages", response_model=List[WebPagePublic])
def list_web_pages(category_id: Optional[int] = None, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    query = select(WebPage)
    if category_id:
        query = query.where(WebPage.category_id == category_id)
    pages = session.exec(query).all()
    return [
        WebPagePublic(
            id=p.id,
            category_id=p.category_id,
            url=p.url,
            account=p.account,
            password=p.password,
            cookie=p.cookie,
            note=p.note,
        )
        for p in pages
    ]


@app.delete("/web/pages/{page_id}", status_code=204)
def delete_web_page(page_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    page = session.get(WebPage, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="网页记录不存在")
    session.delete(page)
    session.commit()
    logging.info("删除网页：%s", page.url)
    return None


@app.get("/summary")
def summary(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    total_balance = sum(user.balance for user in users)
    models = session.exec(select(ModelConfig)).all()
    return {"user_count": len(users), "total_balance": total_balance, "model_count": len(models)}


@app.get("/roles")
def list_roles(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    stats: Dict[str, int] = {role.value: 0 for role in Role}
    for u in users:
        stats[u.role] = stats.get(u.role, 0) + 1
    return {"roles": stats}


@app.get("/role-prompts", response_model=List[RolePromptPublic])
def list_role_prompts(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    prompts = session.exec(select(RolePrompt).order_by(RolePrompt.id)).all()
    return [RolePromptPublic(id=p.id, name=p.name, prompt=p.prompt) for p in prompts]


@app.post("/role-prompts", response_model=RolePromptPublic, status_code=status.HTTP_201_CREATED)
def create_role_prompt(payload: RolePromptCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    existing = session.exec(select(RolePrompt).where(RolePrompt.name == payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="提示词名称已存在")
    record = RolePrompt(name=payload.name, prompt=payload.prompt)
    session.add(record)
    session.commit()
    session.refresh(record)
    logging.info("新增提示词角色：%s", record.name)
    return RolePromptPublic(id=record.id, name=record.name, prompt=record.prompt)


@app.put("/role-prompts/{prompt_id}", response_model=RolePromptPublic)
def update_role_prompt(prompt_id: int, payload: RolePromptUpdate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    record = session.get(RolePrompt, prompt_id)
    if not record:
        raise HTTPException(status_code=404, detail="提示词不存在")

    if payload.name and payload.name != record.name:
        exists = session.exec(select(RolePrompt).where(RolePrompt.name == payload.name)).first()
        if exists:
            raise HTTPException(status_code=400, detail="提示词名称已存在")
        record.name = payload.name
    if payload.prompt is not None:
        record.prompt = payload.prompt

    session.add(record)
    session.commit()
    session.refresh(record)
    logging.info("更新提示词角色：%s", record.name)
    return RolePromptPublic(id=record.id, name=record.name, prompt=record.prompt)


@app.delete("/role-prompts/{prompt_id}", status_code=204)
def delete_role_prompt(prompt_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    record = session.get(RolePrompt, prompt_id)
    if not record:
        raise HTTPException(status_code=404, detail="提示词不存在")
    session.delete(record)
    session.commit()
    logging.info("删除提示词角色：%s", record.name)
    return None


def read_logs(max_lines: int = 200) -> List[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]


@app.get("/logs")
def get_logs(limit: int = 200, _: User = Depends(require_admin)):
    return {"lines": read_logs(max_lines=max(10, min(limit, 1000)))}


@app.post("/roles/assign")
def assign_role(payload: RoleUpdate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = payload.role.value
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.get("/stats/redis")
def redis_stats():
    return {"register_count": get_register_count(), "online_count": get_online_count()}


@app.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    summary_data = summary(session, _)  # type: ignore[arg-type]
    now = dt.datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    weather = "晴朗"
    return {
        "summary": summary_data,
        "redis": redis_stats(),
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "ip": client_ip,
        "weather": weather,
    }


@app.get("/job-helper/config", response_model=JobAutomationConfigPublic)
def get_job_helper_config(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_job_config(session)


@app.put("/job-helper/config", response_model=JobAutomationConfigPublic)
def update_job_helper_config(
    payload: JobAutomationConfigUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    config = get_job_config(session)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(config, field, value)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@app.post("/job-helper/run", response_model=JobRunPublic)
def trigger_job_helper(
    payload: JobRunRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    config = get_job_config(session)
    merged = merge_job_config(config, payload)

    job_run = JobRun(
        status="pending",
        message="正在提交到 get_jobs...",
        requested_by=user.id,
        keywords=merged.keywords,
        cities=merged.cities,
        resume_link=merged.resume_link,
        greeting=merged.greeting,
        auto_apply=merged.auto_apply,
        auto_greet=merged.auto_greet,
        daily_limit=merged.daily_limit,
    )
    session.add(job_run)
    session.commit()
    session.refresh(job_run)

    try:
        reply_text = call_get_jobs(config=config, merged=merged)
        job_run.status = "success"
        job_run.message = reply_text or "提交成功"
    except HTTPException as exc:
        job_run.status = "failed"
        job_run.message = str(exc.detail)
        job_run.finished_at = datetime.utcnow()
        session.add(job_run)
        session.commit()
        session.refresh(job_run)
        raise

    job_run.finished_at = datetime.utcnow()
    session.add(job_run)
    session.commit()
    session.refresh(job_run)
    return job_run


@app.get("/job-helper/runs", response_model=List[JobRunPublic])
def list_job_runs(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    statement = select(JobRun).order_by(JobRun.requested_at.desc()).limit(50)
    return list(session.exec(statement))
