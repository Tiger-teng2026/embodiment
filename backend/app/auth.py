import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.errors import api_error

bearer = HTTPBearer(auto_error=False)


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise api_error(401, "UNAUTHORIZED")
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise api_error(401, "UNAUTHORIZED") from exc
    username = payload.get("sub")
    if not isinstance(username, str) or username != settings.admin_username:
        raise api_error(401, "UNAUTHORIZED")
    return username


def credentials_match(username: str, password: str) -> bool:
    if not settings.admin_username or not settings.admin_password:
        return False
    name_ok = hmac.compare_digest(username.encode("utf-8"), settings.admin_username.encode("utf-8"))
    pass_ok = hmac.compare_digest(password.encode("utf-8"), settings.admin_password.encode("utf-8"))
    return name_ok and pass_ok
