import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import jwt
from app.config import settings

def hash_password(password: str) -> str:
    # bcrypt only supports up to 72 bytes
    pwd_bytes = password.encode("utf-8")[:72].decode("utf-8", errors="ignore").encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore").encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()

def verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
    return hash_otp(plain_otp) == hashed_otp

def generate_otp(length: int = 6) -> str:
    # 6-digit numeric OTP
    return "".join(secrets.choice("0123456789") for _ in range(length))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
