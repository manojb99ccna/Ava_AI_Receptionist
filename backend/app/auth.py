import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Admin

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

bearer = HTTPBearer(auto_error=False)


def md5(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()


def create_token(admin: Admin) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(admin.id), "exp": expires}, JWT_SECRET, algorithm="HS256")


def current_admin(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Admin:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    if not creds:
        raise unauthorized
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise unauthorized
    admin = db.get(Admin, int(payload["sub"]))
    if not admin:
        raise unauthorized
    return admin
