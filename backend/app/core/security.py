"""安全相关工具。"""

from __future__ import annotations

import hashlib
import secrets


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def generate_salt() -> str:
    return secrets.token_hex(8)
