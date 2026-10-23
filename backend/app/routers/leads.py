from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import AvaLead, Admin
from ..auth import current_admin

router = APIRouter(prefix="/api/admin/leads", tags=["admin-leads"])

class LeadResponse(BaseModel):
    id: int
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    requested_service: str | None = None
    preferred_datetime: str | None = None
    status: str
    source: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True

@router.get("", response_model=List[LeadResponse])
def get_admin_leads(
    db: Session = Depends(get_db), 
    admin: Admin = Depends(current_admin)
):
    """
    Fetch all captured leads from the ava_leads table.
    Protected by admin authentication.
    """
    try:
        leads = db.query(AvaLead).order_by(AvaLead.created_at.desc()).all()
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))