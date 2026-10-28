"""
auth.py
Lightweight, cryptographically secure authentication service using Python standard library.
Implements PBKDF2-HMAC-SHA256 password hashing and HMAC-SHA256 signed bearer tokens.
Does not require external passlib, bcrypt, or PyJWT dependencies.
"""

import os
import json
import hmac
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.core.config import settings

# Secret key for HMAC token signing
AUTH_SECRET = os.getenv("AUTH_SECRET_KEY", "aicte-regulatory-auth-secret-key-aph-2026-secure-random")
TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored PBKDF2 or SHA256 hash."""
    if not hashed_password or not plain_password:
        return False

    # 1. PBKDF2 format: pbkdf2:sha256:iterations$salt$hash
    if hashed_password.startswith("pbkdf2:sha256:"):
        try:
            parts = hashed_password.split("$")
            meta = parts[0].split(":")
            iterations = int(meta[2])
            salt = parts[1]
            stored_key = parts[2]
            computed_key = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            ).hex()
            return hmac.compare_digest(stored_key, computed_key)
        except Exception:
            return False

    # 2. Plain SHA256 hex fallback
    if len(hashed_password) == 64:
        computed_sha = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(hashed_password, computed_sha)

    # 3. Direct plaintext comparison fallback for legacy dev fixtures
    return hmac.compare_digest(hashed_password, plain_password)


def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates an HMAC-SHA256 signed bearer token containing user claims and expiration timestamp.
    Token structure: base64(header).base64(payload).signature
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        **user_data,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    message = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(AUTH_SECRET.encode(), message, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies the HMAC-SHA256 signature and expiration of a bearer token.
    Returns decoded payload claims if valid, None otherwise.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode()

        # Add padding back if necessary
        sig_padding = len(sig_b64) % 4
        if sig_padding:
            sig_b64 += "=" * (4 - sig_padding)
        provided_sig = base64.urlsafe_b64decode(sig_b64.encode())

        expected_sig = hmac.new(AUTH_SECRET.encode(), message, hashlib.sha256).digest()
        if not hmac.compare_digest(provided_sig, expected_sig):
            return None

        payload_padding = len(payload_b64) % 4
        if payload_padding:
            payload_b64 += "=" * (4 - payload_padding)
        payload_data = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())

        # Check expiration
        exp = payload_data.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None

        return payload_data
    except Exception:
        return None
