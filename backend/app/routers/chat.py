
from fastapi import APIRouter
from pydantic import BaseModel

import os
import json
import uuid
import joblib

from app.database import SessionLocal
from app.models import AvaConversation, AvaMessage,AvaBusinessFAQ, AvaLead

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


router = APIRouter(prefix="/api/chat", tags=["chat"])

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "artifacts",
    "intent_model.joblib",
)

intent_artifacts = joblib.load(MODEL_PATH)
vectorizer = intent_artifacts["vectorizer"]
model = intent_artifacts["model"]


def get_or_create_conversation(db, session_id: str):
    conversation = (
        db.query(AvaConversation)
        .filter(AvaConversation.session_id == session_id)
        .first()
    )

    if conversation:
        return conversation

    conversation = AvaConversation(
        session_id=session_id,
        intent=None,
        current_step=None,
        lead_data=json.dumps({})
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None




def match_faq(db, user_message: str, detected_intent: str):
    # 1. Fetch all active FAQs from MySQL
    faqs = db.query(AvaBusinessFAQ).filter(AvaBusinessFAQ.is_active == True).all()
    if not faqs:
        return None

    # 2. Extract stored questions from database objects
    faq_questions = [faq.question for faq in faqs]
    
    # 3. Build a TF-IDF corpus combining stored FAQs and the user's message
    corpus = faq_questions + [user_message]
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
    
    faq_vectors = tfidf_matrix[:-1]
    user_vector = tfidf_matrix[-1]

    # 4. Compute cosine similarity scores
    similarities = cosine_similarity(user_vector, faq_vectors).flatten()
    best_match_idx = similarities.argmax()
    best_score = similarities[best_match_idx]

    # 5. Apply a confidence threshold (e.g., 0.20)
    THRESHOLD = 0.20
    if best_score >= THRESHOLD:
        return faqs[best_match_idx].answer

    return None


 



@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        return {
            "reply": "Please enter a message.",
            "session_id": request.session_id,
        }

    session_id = request.session_id or str(uuid.uuid4())
    db = SessionLocal()

    try:
        conversation = get_or_create_conversation(db, session_id)

        # 1. Detect intent using ML model
        X = vectorizer.transform([message])
        intent = model.predict(X)[0]
        conversation.intent = intent

        current_step = conversation.current_step
        lead_data = json.loads(conversation.lead_data or "{}")
        reply = ""

        # --- PHASE 1.5 & 1.6: WORKFLOW STATE MACHINE ---
        if current_step == "collecting_name":
            lead_data["name"] = message
            conversation.current_step = "collecting_phone"
            conversation.lead_data = json.dumps(lead_data)
            db.commit()
            reply = f"Thanks, {message}! What is the best phone number to reach you?"

        elif current_step == "collecting_phone":
            lead_data["phone"] = message
            conversation.current_step = "collecting_service"
            conversation.lead_data = json.dumps(lead_data)
            db.commit()
            reply = "Got it. What service or project are you interested in?"

        elif current_step == "collecting_service":
            lead_data["service"] = message
            conversation.current_step = "collecting_datetime"
            conversation.lead_data = json.dumps(lead_data)
            db.commit()
            reply = "When would you prefer to schedule this consultation? (e.g., Tomorrow at 2 PM)"

        elif current_step == "collecting_datetime":
            lead_data["datetime"] = message
            
            # Save to ava_leads table (Phase 1.6)
            new_lead = AvaLead(
                name=lead_data.get("name"),
                phone=lead_data.get("phone"),
                email=None,
                requested_service=lead_data.get("service"),
                preferred_datetime=lead_data.get("datetime"),
                status="new",
                source="website_chat"
            )
            db.add(new_lead)
            
            # Reset conversation state
            conversation.current_step = None
            conversation.lead_data = json.dumps({})
            db.commit()
            
            reply = f"You're all set, {lead_data.get('name')}! I've successfully saved your request. Our team will contact you shortly."

        else:
            # Check if user triggered booking intent or keywords
            if intent == "appointment" or any(kw in message.lower() for kw in ["appointment", "schedule", "book", "meeting"]):
                conversation.current_step = "collecting_name"
                db.commit()
                reply = "I would love to help you schedule a consultation! To get started, what is your full name?"
            else:
                # 1. Attempt database-driven FAQ matching from ava_business_faqs
                faq_answer = match_faq(db, message, intent)
                if faq_answer:
                    reply = faq_answer
                else:
                    # 2. Graceful fallback for non-FAQ intents (like greetings or general chat)
                    if intent == "greeting":
                        reply = "Hello! Welcome to WebeXcellence. How can I assist you with our services today?"
                    elif intent == "goodbye":
                        reply = "Goodbye! Feel free to reach out if you have any more questions. Have a great day!"
                    elif intent == "human_escalation":
                        reply = "I can definitely connect you with a member of our team. Would you like to schedule a callback or leave your contact details?"
                    else:
                        reply = "I'd be happy to help you with that. Would you like to schedule a consultation or check out our services?"

        # Save user's message
        db.add(AvaMessage(
            conversation_id=conversation.id,
            sender="user",
            message=message,
        ))

        # Save Ava's reply
        db.add(AvaMessage(
            conversation_id=conversation.id,
            sender="ava",
            message=reply,
        ))

        db.commit()

        return {
            "reply": reply,
            "session_id": session_id,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()