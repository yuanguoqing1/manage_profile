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
import os
import secrets
from enum import Enum
from typing import Dict, List, Optional

try:
    import redis
except ImportError:  # pragma: no cover - 在无依赖环境下自动降级
    redis = None  # type: ignore
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select


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


class ApiKey(SQLModel, table=True):
    """API Key 表"""

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(index=True)
    key: str = Field(unique=True, index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")


class ApiKeyCreate(SQLModel):
    label: str
    key: str
    owner_id: Optional[int] = None


class ApiKeyPublic(SQLModel):
    id: int
    label: str
    key: str
    owner_id: Optional[int]


class LoginRequest(SQLModel):
    """登录入参"""

    name: str
    password: str


class LoginResponse(SQLModel):
    token: str
    user: UserPublic


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


@app.post("/apikeys", response_model=ApiKeyPublic, status_code=status.HTTP_201_CREATED)
def create_key(key: ApiKeyCreate, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    existing = session.exec(select(ApiKey).where(ApiKey.key == key.key)).first()
    if existing:
        raise HTTPException(status_code=400, detail="API key already exists")
    if key.owner_id and not session.get(User, key.owner_id):
        raise HTTPException(status_code=404, detail="Owner not found")
    api_key = ApiKey(label=key.label, key=key.key, owner_id=key.owner_id)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return ApiKeyPublic(id=api_key.id, label=api_key.label, key=api_key.key, owner_id=api_key.owner_id)


@app.get("/apikeys", response_model=List[ApiKeyPublic])
def list_keys(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    keys = session.exec(select(ApiKey)).all()
    return [ApiKeyPublic(id=k.id, label=k.label, key=k.key, owner_id=k.owner_id) for k in keys]


@app.get("/apikeys/{key_id}", response_model=ApiKeyPublic)
def get_key(key_id: int, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    key = session.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyPublic(id=key.id, label=key.label, key=key.key, owner_id=key.owner_id)


@app.delete("/apikeys/{key_id}", status_code=204)
def delete_key(key_id: int, session: Session = Depends(get_session), _: User = Depends(require_admin)):
    key = session.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    session.delete(key)
    session.commit()
    return None


@app.get("/summary")
def summary(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    total_balance = sum(user.balance for user in users)
    keys = session.exec(select(ApiKey)).all()
    return {
        "user_count": len(users),
        "total_balance": total_balance,
        "api_key_count": len(keys),
    }


@app.get("/roles")
def list_roles(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    stats: Dict[str, int] = {role.value: 0 for role in Role}
    for u in users:
        stats[u.role] = stats.get(u.role, 0) + 1
    return {"roles": stats}


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
