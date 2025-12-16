from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0, ge=0.0)


class ApiKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(index=True)
    key: str = Field(unique=True, index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")


sqlite_url = "sqlite:///./data.db"
# 使用 check_same_thread=False 允许多线程访问 SQLite，避免在并发请求时触发线程安全错误
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


app = FastAPI(title="Profile Manager", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/users", response_model=User, status_code=201)
def create_user(user: User, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.name == user.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User name already exists")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users", response_model=List[User])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}/balance", response_model=User)
def update_balance(user_id: int, amount: float, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_balance = user.balance + amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Balance cannot be negative")
    user.balance = new_balance
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/apikeys", response_model=ApiKey, status_code=201)
def create_key(key: ApiKey, session: Session = Depends(get_session)):
    existing = session.exec(select(ApiKey).where(ApiKey.key == key.key)).first()
    if existing:
        raise HTTPException(status_code=400, detail="API key already exists")
    if key.owner_id and not session.get(User, key.owner_id):
        raise HTTPException(status_code=404, detail="Owner not found")
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@app.get("/apikeys", response_model=List[ApiKey])
def list_keys(session: Session = Depends(get_session)):
    return session.exec(select(ApiKey)).all()


@app.delete("/apikeys/{key_id}", status_code=204)
def delete_key(key_id: int, session: Session = Depends(get_session)):
    key = session.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    session.delete(key)
    session.commit()
    return None


@app.get("/summary")
def summary(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    total_balance = sum(user.balance for user in users)
    keys = session.exec(select(ApiKey)).all()
    return {
        "user_count": len(users),
        "total_balance": total_balance,
        "api_key_count": len(keys),
    }
