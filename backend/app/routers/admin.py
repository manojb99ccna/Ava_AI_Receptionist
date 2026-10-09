from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_token, current_admin, md5
from ..database import get_db
from ..models import Admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginIn(BaseModel):
    username: str
    password: str


def admin_out(admin: Admin) -> dict:
    return {"id": admin.id, "username": admin.username, "name": admin.name}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or admin.password != md5(data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return {"token": create_token(admin), "admin": admin_out(admin)}


@router.get("/me")
def me(admin: Admin = Depends(current_admin)):
    return admin_out(admin)
