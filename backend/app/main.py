from __future__ import annotations

import datetime as dt
import hashlib
import logging
import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import httpx

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore

from datetime import datetime

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, or_, func
from sqlmodel import Field, Session, SQLModel, select

from app.database.session import create_db_and_tables, engine, get_session

LOG_FILE = Path("app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
)


class Role(str, Enum):
    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0, ge=0.0)
    password_hash: str
    salt: str
    role: str = Field(default=Role.user.value, index=True)


class UserCreate(SQLModel):
    name: str
    password: str
    role: Optional[Role] = None


class UserPublic(SQLModel):
    id: int
    name: str
    balance: float
    role: str


class UserContactPublic(SQLModel):
    id: int
    name: str
    role: str


class UserContactStatusPublic(UserContactPublic):
    is_online: bool


class BalanceUpdate(SQLModel):
    amount: float


class ModelConfig(SQLModel, table=True):
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
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")


class WebPage(SQLModel, table=True):
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
    name: str
    password: str


class LoginResponse(SQLModel):
    token: str
    user: UserPublic


class ChatMessage(SQLModel):
    role: str
    content: str


class PeerMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatCompletionRequest(SQLModel):
    model_id: Optional[int] = None
    messages: List[ChatMessage]
    stream: bool = False
    role_prompt: Optional[str] = None
    role_id: Optional[int] = None


UsageValue = Union[int, Dict[str, int]]


class ChatCompletionResponse(SQLModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, object]]
    usage: Dict[str, UsageValue]


class PeerMessageCreate(SQLModel):
    receiver_id: int
    content: str


class PeerMessagePublic(SQLModel):
    id: int
    sender_id: int
    receiver_id: int
    sender_name: str
    receiver_name: str
    content: str
    created_at: datetime


class UserUpdate(SQLModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Role] = None


class ModelConfigUpdate(SQLModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    owner_id: Optional[int] = None


class RolePrompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    prompt: str


class RolePromptCreate(SQLModel):
    name: str
    prompt: str


class RolePromptUpdate(SQLModel):
    name: Optional[str] = None
    prompt: Optional[str] = None


class RolePromptPublic(SQLModel):
    id: int
    name: str
    prompt: str


class RoleUpdate(SQLModel):
    user_id: int
    role: Role


class JobAutomationConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    service_url: str = Field(default="", description="get_jobs 服务接收任务的地址")
    service_token: Optional[str] = Field(default=None, description="get_jobs 服务鉴权 token，可选")
    resume_link: Optional[str] = Field(default=None, description="简历链接或存储地址")
    greeting: str = Field(default="您好，我对岗位很感兴趣，这是我的简历，期待沟通。", description="开场白模板")
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


class AuthToken(SQLModel, table=True):
    token: str = Field(primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


# -----------------------------
# Redis（可选）
# -----------------------------
def init_redis() -> Optional["redis.Redis"]:
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
        logging.warning("Redis 连接失败，将使用数据库统计：%s", exc)
        return None


redis_client = init_redis()
if redis_client:
    logging.info("Redis 连接成功")
else:
    logging.info("Redis 不可用，使用数据库统计在线与注册数量")


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def admin_exists(session: Session) -> bool:
    return session.exec(select(User).where(User.role == Role.admin.value)).first() is not None


def increment_register_count() -> None:
    # Redis 有就自增一个统计值；没有也没关系，注册数可直接从 DB count 得到
    if redis_client:
        redis_client.incr("register_count")


def register_user_online(token: str) -> None:
    # Redis 有就记录 token（只用于“在线计数”用途）；DB 里 AuthToken 才是事实来源
    if redis_client:
        redis_client.sadd("online_tokens", token)


def logout_user_online(token: str) -> None:
    if redis_client:
        redis_client.srem("online_tokens", token)


def purge_expired_tokens(session: Session) -> int:
    now = datetime.utcnow()
    expired = session.exec(select(AuthToken).where(AuthToken.expires_at.is_not(None), AuthToken.expires_at < now)).all()
    for r in expired:
        session.delete(r)
    if expired:
        session.commit()
    return len(expired)


def get_online_count(session: Session) -> int:
    # 优先 Redis（实时），否则用 DB token 数（注意可配合 expires_at 清理）
    if redis_client:
        return int(redis_client.scard("online_tokens"))
    # DB 统计 token 数
    purge_expired_tokens(session)
    return session.exec(select(func.count()).select_from(AuthToken)).one()[0]


def get_register_count(session: Session) -> int:
    # Redis 有就读 Redis；否则用 DB 用户表 count
    if redis_client:
        value = redis_client.get("register_count")
        return int(value) if value else 0
    return session.exec(select(func.count()).select_from(User)).one()[0]


# -----------------------------
# WebSocket 连接管理
# -----------------------------
class ConnectionManager:
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

app = FastAPI(title="Profile Manager", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    logging.info("startup done")


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


# -----------------------------
# Auth helpers
# -----------------------------
def _validate_token_record(record: AuthToken) -> None:
    if record.expires_at is not None and record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期")


def get_current_user(
    authorization: str = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少凭证")
    token = authorization.split()[1]

    record = session.get(AuthToken, token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    _validate_token_record(record)

    user = session.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_user_by_token(token: str, session: Session) -> User:
    record = session.get(AuthToken, token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    _validate_token_record(record)

    user = session.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


# -----------------------------
# WebSocket
# -----------------------------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
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
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc.detail))
            return

        await ws_manager.connect(user.id, ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(user.id, ws)
        except Exception:  # noqa: BLE001
            ws_manager.disconnect(user.id, ws)
            try:
                await ws.close(code=1011)
            except Exception:  # noqa: BLE001
                pass


# -----------------------------
# Auth endpoints
# -----------------------------
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

    # 可选：给 token 加过期时间，比如 7 天
    expires_at = datetime.utcnow() + dt.timedelta(days=7)

    record = AuthToken(token=token, user_id=user.id, expires_at=expires_at)
    session.add(record)
    session.commit()

    register_user_online(token)

    public_user = UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)
    return LoginResponse(token=token, user=public_user)


@app.post("/auth/logout")
def logout(
    authorization: str = Header(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # get_current_user 已校验过 Bearer
    token = authorization.split()[1]

    record = session.get(AuthToken, token)
    if record:
        session.delete(record)
        session.commit()

    logout_user_online(token)
    return {"message": f"{user.name} 已退出"}


@app.get("/auth/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)):
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


# -----------------------------
# Users / Contacts / Messages
# -----------------------------
@app.get("/contacts", response_model=List[UserContactStatusPublic])
def list_contacts(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    purge_expired_tokens(session)
    online_user_ids = {r.user_id for r in session.exec(select(AuthToken)).all()}

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
    await ws_manager.send_to(receiver.id, payload_ws)
    await ws_manager.send_to(user.id, payload_ws)

    return public_msg


# -----------------------------
# Stats / Dashboard
# -----------------------------
@app.get("/stats/redis")
def redis_stats(session: Session = Depends(get_session)):
    return {
        "register_count": get_register_count(session),
        "online_count": get_online_count(session),
    }


@app.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    total_balance = sum(u.balance for u in users)
    models = session.exec(select(ModelConfig)).all()

    now = dt.datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    weather = "晴朗"

    return {
        "summary": {"user_count": len(users), "total_balance": total_balance, "model_count": len(models)},
        "redis": redis_stats(session),
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "ip": client_ip,
        "weather": weather,
        "me": {"id": user.id, "name": user.name, "role": user.role},
    }


# -----------------------------
# Chat completions（保留你原逻辑）
# -----------------------------
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
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"请求上游模型失败：{exc}") from exc

        return StreamingResponse(stream_response(), media_type="text/event-stream")

    try:
        with httpx.Client(timeout=30.0) as client:
            upstream_response = client.post(
                target_url,
                headers={"Authorization": f"Bearer {model.api_key}"},
                json=request_body,
            )
    except httpx.RequestError as exc:
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


# -----------------------------
# Logs
# -----------------------------
def read_logs(max_lines: int = 200) -> List[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]


@app.get("/logs")
def get_logs(limit: int = 200, _: User = Depends(require_admin)):
    return {"lines": read_logs(max_lines=max(10, min(limit, 1000)))}
