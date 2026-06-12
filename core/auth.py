"""
auth.py
User registration, login, and JWT verification.
Users are persisted in users.json (project root).
"""

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import config

_USERS_FILE = "users.json"
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 24 * 7  # one week

_http_bearer = HTTPBearer()


# ── Persistence ──────────────────────────────────────────────────────────────────

def _load_users() -> dict:
    if not os.path.exists(_USERS_FILE):
        return {}
    with open(_USERS_FILE) as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Public API ───────────────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> str:
    """Create a new user and return their user_id."""
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    users = _load_users()
    if username in users:
        raise ValueError("Username already taken")
    user_id = secrets.token_hex(8)
    users[username] = {"user_id": user_id, "password_hash": _hash(password)}
    _save_users(users)
    return user_id


def authenticate_user(username: str, password: str) -> str:
    """Verify credentials and return user_id, or raise ValueError."""
    users = _load_users()
    record = users.get(username)
    if not record or record["password_hash"] != _hash(password):
        raise ValueError("Invalid username or password")
    return record["user_id"]


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_http_bearer),
) -> str:
    """FastAPI dependency — returns user_id from a valid Bearer token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            config.SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
