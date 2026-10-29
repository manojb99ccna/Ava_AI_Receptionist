import os
import time
import traceback
from fastapi import Request
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from .auth import md5
from .database import Base, SessionLocal, engine
from .models import Admin, AvaConversation, AvaMessage
from .routers import admin, chat, leads, conversations, faqs
from app.utils.logger import log_debug_data

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
app.include_router(leads.router)
app.include_router(conversations.router)
app.include_router(faqs.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Globally catches ANY unhandled exception, crash, or 500 error 
    from any file in the entire project and logs it automatically.
    """
    error_details = {
        "path": request.url.path,
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc()
    }
    # Automatically writes to your debug log file without touching individual endpoints
    log_debug_data("GLOBAL PROJECT ERROR", error_details, type="info")
    
    # Return a clean 500 response to the client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check debug logs for details."},
    )



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