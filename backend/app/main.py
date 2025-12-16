"""
应用主入口：提供用户、API Key、认证、角色管理与仪表盘统计接口。

设计要点：
- 使用内置 token 简易鉴权，避免引入 JWT 依赖；密码通过 PBKDF2 哈希存储。
- Redis 用于记录注册总数与在线人数，若 Redis 不可用则自动降级为内存计数。
- 提供角色管理（admin/user），管理员可进行增删改，普通用户仅查看公共数据。
"""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import os
import secrets
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional

import httpx

try:
    import redis
except ImportError:  # pragma: no cover - 在无依赖环境下自动降级
    redis = None  # type: ignore
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
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


class ChatCompletionRequest(SQLModel):
    """聊天请求参数"""

    model_id: Optional[int] = None
    messages: List[ChatMessage]


class ChatCompletionResponse(SQLModel):
    """与 OpenAI 对齐的返回体"""

    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, object]]
    usage: Dict[str, int]


class RoleUpdate(SQLModel):
    """角色赋予入参"""

    user_id: int
    role: Role


sqlite_url = "sqlite:///./data.db"
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

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
            existing = {
                row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info(\"{table}\")").all()
            }
            for column, sql_type in columns.items():
                if column not in existing:
                    conn.exec_driver_sql(
                        f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"  # noqa: S608
                    )


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    ensure_columns()


def get_session():
    with Session(engine) as session:
        yield session


def init_redis() -> Optional[redis.Redis]:
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
def logout(
    authorization: str = Header(default=None), user: User = Depends(get_current_user)
):
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
    user = User(
        name=user_in.name, balance=0.0, password_hash=password_hash, salt=salt, role=role_value
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    increment_register_count()
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.get("/users", response_model=List[UserPublic])
def list_users(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    return [UserPublic(id=u.id, name=u.name, balance=u.balance, role=u.role) for u in users]


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(id=user.id, name=user.name, balance=user.balance, role=user.role)


@app.put("/users/{user_id}/balance", response_model=UserPublic)
def update_balance(
    user_id: int,
    update: BalanceUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
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
def create_model_config(
    key: ModelConfigCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
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
def get_model_config(
    model_id: int, session: Session = Depends(get_session), _: User = Depends(get_current_user)
):
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


@app.delete("/models/{model_id}", status_code=204)
def delete_model_config(
    model_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
    model = session.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    session.delete(model)
    session.commit()
    logging.info("删除大模型配置：%s", model.name)
    return None


@app.post("/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(
    payload: ChatCompletionRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
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
    request_body = {
        "model": model.model_name,
        "messages": [msg.model_dump() for msg in payload.messages],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            upstream_response = client.post(
                target_url,
                headers={"Authorization": f"Bearer {model.api_key}"},
                json=request_body,
            )
    except httpx.RequestError as exc:  # pragma: no cover - 网络异常依赖外部环境
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
    data.setdefault(
        "usage",
        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )
    return data


@app.post("/web/categories", response_model=WebCategoryPublic, status_code=status.HTTP_201_CREATED)
def create_web_category(
    payload: WebCategoryCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
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
def list_web_categories(
    session: Session = Depends(get_session), _: User = Depends(get_current_user)
):
    categories = session.exec(select(WebCategory)).all()
    return [WebCategoryPublic(id=c.id, name=c.name, description=c.description) for c in categories]


@app.delete("/web/categories/{category_id}", status_code=204)
def delete_web_category(
    category_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
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
def create_web_page(
    payload: WebPageCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
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
def list_web_pages(
    category_id: Optional[int] = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
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
def delete_web_page(
    page_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)
):
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
    return {
        "user_count": len(users),
        "total_balance": total_balance,
        "model_count": len(models),
    }


@app.get("/roles")
def list_roles(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    stats: Dict[str, int] = {role.value: 0 for role in Role}
    for u in users:
        stats[u.role] = stats.get(u.role, 0) + 1
    return {"roles": stats}


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
    weather = "晴朗"  # 占位天气，避免依赖外部服务
    return {
        "summary": summary_data,
        "redis": redis_stats(),
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "ip": client_ip,
        "weather": weather,
    }
