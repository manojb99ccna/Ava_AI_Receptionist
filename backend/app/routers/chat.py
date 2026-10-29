from fastapi import APIRouter
from pydantic import BaseModel
import os
import json
import uuid
import joblib
from app.database import SessionLocal
from app.models import AvaConversation, AvaMessage, AvaBusinessFAQ, AvaLead
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import pprint
from app.utils.logger import log_debug_data

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


def model_to_dict(obj):
    """
    Safely converts any SQLAlchemy model instance into a dictionary 
    so it can be printed and formatted with pprint in debug logs.
    """
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def is_valid_phone(phone: str) -> bool:
    # Removes spaces/dashes and checks if there are between 10 and 15 digits
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15

def is_valid_name(name: str) -> bool:
    name_clean = name.strip()
    name_lower = name_clean.lower()
    
    # 1. Check length boundaries (minimum 2 chars, maximum 40 chars)
    if len(name_clean) < 2 or len(name_clean) > 40:
        return False
        
    # 2. Reject common conversational fillers and command phrases
    invalid_phrases = [
        "yes", "no", "yeah", "nope", "mistake", "wait", "ok", "cancel",
        "tell me about yourself", "who are you", "what do you do", 
        "hi", "hello", "hey", "help"
    ]
    if name_lower in invalid_phrases:
        return False
        
    words = name_clean.split()
    
    # 3. Ensure a name isn't too many words (e.g., max 4 words for a full name)
    if len(words) > 4:
        return False
        
    # 4. Check for suspicious question/command words inside the input
    forbidden_words = ["tell", "about", "yourself", "what", "who", "how", "why", "where", "can", "do"]
    if any(word in name_lower for word in forbidden_words) and len(words) > 1:
        return False
        
    # 5. Ensure it doesn't contain numbers
    if any(char.isdigit() for char in name_clean):
        return False
    return True

def is_valid_datetime(dt_str: str) -> bool:
    dt_clean = dt_str.strip().lower()
    
    # Reject conversational fillers or extremely short strings
    invalid_words = ["no", "cancel", "stop", "nope", "skip", "none"]
    if dt_clean in invalid_words or len(dt_clean) < 3:
        return False
        
    time_keywords = [
        "tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", 
        "friday", "saturday", "sunday", "am", "pm", "morning", "afternoon", 
        "evening", "night", "now", "soon", "at", ":"
    ]
    
    has_digits = any(char.isdigit() for char in dt_clean)
    has_keyword = any(kw in dt_clean for kw in time_keywords)
    
    return has_digits or has_keyword or len(dt_clean) >= 5


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

    log_debug_data("Step 1: FAQ Corpus for TF-IDF", {"corpus": corpus, "detected_intent": detected_intent}, type="chat_faq")


    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)


    log_debug_data(
        "Step 2: TF-IDF Matrix",
        {
            "tfidf_matrix_shape": tfidf_matrix.shape,
            "detected_intent": detected_intent
        },
        type="chat_faq"
    )
    
    faq_vectors = tfidf_matrix[:-1]
    user_vector = tfidf_matrix[-1]

    # 4. Compute cosine similarity scores
    similarities = cosine_similarity(user_vector, faq_vectors).flatten()
    best_match_idx = similarities.argmax()
    best_score = similarities[best_match_idx]

    # 5. Apply a confidence threshold
    THRESHOLD = 0.20
    if best_score >= THRESHOLD:
        return faqs[best_match_idx].answer

    return None


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()

    log_debug_data("Step 1: User Message Received", {"message": message, "session_id": request.session_id})

    if not message:
        return {
            "reply": "Please enter a message.",
            "session_id": request.session_id,
        }

    session_id = request.session_id or str(uuid.uuid4())
    db = SessionLocal()

    try:
        conversation = get_or_create_conversation(db, session_id)

        log_debug_data("Step 2: Conversation State Before Processing",  {
            "conversation_id": conversation.id,
            "intent": conversation.intent,
            "current_step": conversation.current_step,
            "lead_data": json.loads(conversation.lead_data) if conversation.lead_data else {},
            "full_data": model_to_dict(conversation)
        })

        # 1. Detect intent using ML model
        X = vectorizer.transform([message])
        #intent = model.predict(X)[0]
        intent = str(model.predict(X)[0])

        log_debug_data("Step 2a: Intent Detected by ML Model", {"intent": intent, "message": message, "X_vector": X.toarray().tolist()})

        # --- SMART KEYWORD OVERRIDES --- 
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["price", "pricing", "cost", "charge", "charges", "rate", "rates"]):
            intent = "pricing"
        elif any(kw in msg_lower for kw in ["service", "services", "offer", "do you do", "build"]):
            intent = "services"
        elif any(kw in msg_lower for kw in ["hour", "hours", "open", "close", "weekend"]):
            intent = "business_hours"
        elif any(kw in msg_lower for kw in ["contact", "email", "phone", "reach", "call"]):
            intent = "contact" 

        conversation.intent = intent

        log_debug_data("Step 3: Intent Detected", {"intent": intent})

        current_step = conversation.current_step
        lead_data = json.loads(conversation.lead_data) if conversation.lead_data else {}
        reply = ""

        # --- WORKFLOW STATE MACHINE & VALIDATION ---
        log_debug_data("Step 4: Processing Conversation Step", {"current_step": conversation.current_step})
        if conversation.current_step == "collecting_name":
            if not is_valid_name(message):
                reply = "That doesn't look like a valid name. Could you please provide your full name?"
            else:
                lead_data["name"] = message
                conversation.lead_data = json.dumps(lead_data)
                conversation.current_step = "collecting_phone"
                db.commit()
                reply = f"Thanks, {message}! Now, could you please provide your phone number?"

        elif conversation.current_step == "collecting_phone":
            if not is_valid_phone(message):
                reply = "That doesn't look like a valid phone number. Please enter a valid 10-digit phone number so we can reach you."
            else:
                lead_data["phone"] = message
                conversation.lead_data = json.dumps(lead_data)
                conversation.current_step = "collecting_service"
                db.commit()
                reply = "Great! What service are you interested in?"

        elif conversation.current_step == "collecting_service":
            lead_data["requested_service"] = message
            conversation.lead_data = json.dumps(lead_data)
            conversation.current_step = "collecting_datetime"
            db.commit()
            reply = "When would you prefer to schedule this consultation? (e.g., Tomorrow at 2 PM)"

        elif conversation.current_step == "collecting_datetime":
            if not is_valid_datetime(message):
                reply = "Please provide a preferred date or time (e.g., 'Tomorrow at 2 PM' or 'Monday morning') so we can schedule your appointment."
            else:
                lead_data["preferred_datetime"] = message
                conversation.lead_data = json.dumps(lead_data)
                
                name = lead_data.get("name", "Valued Customer")
                phone = lead_data.get("phone", "")
                service = lead_data.get("requested_service", "General Inquiry")
                preferred_dt = lead_data.get("preferred_datetime", "")
                
                new_lead = AvaLead(
                    name=name,
                    phone=phone,
                    requested_service=service,
                    preferred_datetime=preferred_dt,
                    status="new",
                    source="website_chat"
                )
                db.add(new_lead)
                
                conversation.current_step = None
                conversation.intent = None
                db.commit()
                
                log_debug_data("Step 5: Appointment Scheduled", {"lead": new_lead})

                reply = f"You're all set, {name}! I've successfully saved your request. Our team will contact you shortly."

        else:
            if intent == "appointment" or any(kw in msg_lower for kw in ["appointment", "schedule", "book", "meeting"]):
                conversation.current_step = "collecting_name"
                db.commit()
                reply = "I would love to help you schedule a consultation! To get started, what is your full name?"
            else:
                faq_answer = match_faq(db, message, intent)

                log_debug_data("Step 6: FAQ Matching Result", {"faq_answer": faq_answer, "intent": intent})

                if faq_answer:
                    reply = faq_answer
                else:
                    if intent == "greeting":
                        reply = "Hello! Welcome to WebeXcellence. How can I assist you with our services today?"
                    elif intent == "goodbye":
                        reply = "Goodbye! Feel free to reach out if you have any more questions. Have a great day!"
                    elif intent == "human_escalation":
                        reply = "I can definitely connect you with a member of our team. Would you like to schedule a callback or leave your contact details?"
                    else:
                        reply = "I'd be happy to help you with that. Would you like to schedule a consultation or check out our services?"

        log_debug_data("Step 7: Saving User Message", {"message": message, "conversation_id": conversation.id})
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

        log_debug_data("Step 8: Committing Changes", {"conversation_id": conversation.id})
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