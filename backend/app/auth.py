"""
JWT Authentication — backed by DynamoDB (carbon-intelligence-users table).
Demo credentials: company@gmail.com / company@123
Falls back to local JSON if DynamoDB is unavailable.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "carbon-intelligence-secret-key-2024-enterprise")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context  = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Fallback file (used only when DynamoDB is unreachable)
USERS_FILE = Path(__file__).parent.parent / "users.json"


# ── Pydantic models ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    user_name: str
    role: str


class UserInfo(BaseModel):
    email: str
    name: str
    role: str


# ── DynamoDB helpers (with JSON fallback) ─────────────────────────────────────

def _dynamo_get(email: str) -> Optional[dict]:
    try:
        from .dynamodb import get_user
        return get_user(email)
    except Exception as e:
        logger.warning(f"DynamoDB unavailable, using local fallback: {e}")
        return _file_get(email)


def _dynamo_put(user: dict):
    try:
        from .dynamodb import put_user
        put_user(user)
        return
    except Exception as e:
        logger.warning(f"DynamoDB unavailable, using local fallback: {e}")
    _file_put(user)


def _dynamo_exists(email: str) -> bool:
    return _dynamo_get(email) is not None


# ── Local JSON fallback ───────────────────────────────────────────────────────

def _file_load() -> dict:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _file_get(email: str) -> Optional[dict]:
    return _file_load().get(email.lower())


def _file_put(user: dict):
    users = _file_load()
    users[user["email"]] = user
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"File fallback write failed: {e}")


def _ensure_demo_user():
    """Seed the demo account if it doesn't exist yet."""
    email = "company@gmail.com"
    if not _dynamo_exists(email):
        _dynamo_put({
            "email": email,
            "name": "Demo Company",
            "hashed_password": pwd_context.hash("company@123"),
            "role": "admin",
        })


# ── Core auth functions ───────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    _ensure_demo_user()
    user = _dynamo_get(email.lower())
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def register_user(email: str, name: str, password: str) -> dict:
    email = email.lower()
    if _dynamo_exists(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = {
        "email": email,
        "name": name,
        "hashed_password": hash_password(password),
        "role": "user",
    }
    _dynamo_put(user)
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserInfo:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = _dynamo_get(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserInfo(email=user["email"], name=user["name"], role=user["role"])
