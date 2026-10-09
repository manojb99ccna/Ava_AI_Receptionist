import os
import time

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from .auth import md5
from .database import Base, SessionLocal, engine
from .models import Admin
from .routers import admin, chat

app = FastAPI(title="Ava AI Receptionist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(chat.router)


@app.on_event("startup")
def init_db():
    # MySQL may still be starting up; retry for ~30s before giving up
    for attempt in range(15):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            if attempt == 14:
                raise
            time.sleep(2)

    with SessionLocal() as db:
        if not db.query(Admin).first():
            db.add(Admin(
                username=os.getenv("ADMIN_USERNAME", "admin"),
                password=md5(os.getenv("ADMIN_PASSWORD", "admin123")),
                name="Administrator",
            ))
            db.commit()


@app.get("/api/health")
def health():
    return {"status": "ok"}
