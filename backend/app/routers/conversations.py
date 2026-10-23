from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import AvaConversation, AvaMessage, Admin
from ..auth import current_admin

router = APIRouter(prefix="/api/admin/conversations", tags=["admin-conversations"])

class ConversationResponse(BaseModel):
    id: int
    session_id: str
    intent: str | None = None
    current_step: str | None = None
    lead_data: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    message: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True

@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db), 
    admin: Admin = Depends(current_admin)
):
    """Fetch all past chat conversation sessions."""
    try:
        conversations = db.query(AvaConversation).order_by(AvaConversation.updated_at.desc()).all()
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(current_admin)
):
    """Fetch all messages/transcript for a specific conversation session."""
    try:
        messages = db.query(AvaMessage).filter(AvaMessage.conversation_id == conversation_id).order_by(AvaMessage.created_at.asc()).all()
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))