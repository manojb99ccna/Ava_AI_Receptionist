from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import AvaBusinessFAQ, Admin
from ..auth import current_admin

router = APIRouter(prefix="/api/admin/faqs", tags=["admin-faqs"])

class FAQCreateUpdate(BaseModel):
    intent: str
    question: str
    answer: str
    is_active: Optional[bool] = True

class FAQResponse(BaseModel):
    id: int
    intent: str
    question: str
    answer: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

@router.get("", response_model=List[FAQResponse])
def get_faqs(
    db: Session = Depends(get_db), 
    admin: Admin = Depends(current_admin)
):
    """Fetch all business FAQs."""
    try:
        faqs = db.query(AvaBusinessFAQ).order_by(AvaBusinessFAQ.id.desc()).all()
        return faqs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=FAQResponse)
def create_faq(
    faq_data: FAQCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(current_admin)
):
    """Create a new business FAQ."""
    try:
        new_faq = AvaBusinessFAQ(
            intent=faq_data.intent,
            question=faq_data.question,
            answer=faq_data.answer,
            is_active=faq_data.is_active
        )
        db.add(new_faq)
        db.commit()
        db.refresh(new_faq)
        return new_faq
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{faq_id}", response_model=FAQResponse)
def update_faq(
    faq_id: int,
    faq_data: FAQCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(current_admin)
):
    """Update an existing business FAQ."""
    try:
        faq = db.query(AvaBusinessFAQ).filter(AvaBusinessFAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        faq.intent = faq_data.intent
        faq.question = faq_data.question
        faq.answer = faq_data.answer
        faq.is_active = faq_data.is_active
        
        db.commit()
        db.refresh(faq)
        return faq
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{faq_id}")
def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(current_admin)
):
    """Delete a business FAQ."""
    try:
        faq = db.query(AvaBusinessFAQ).filter(AvaBusinessFAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        db.delete(faq)
        db.commit()
        return {"success": True, "message": "FAQ deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))