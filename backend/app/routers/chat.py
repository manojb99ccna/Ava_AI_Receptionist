
from fastapi import APIRouter
from pydantic import BaseModel, Field
import os
import json
import uuid
import joblib
import re

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.models import (
    AvaConversation,
    AvaMessage,
    AvaBusinessFAQ,
    AvaLead,
    AvaAppointment,
    AvaBusinessSetting,
    AvaBusinessWorkingHour,
)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


# ---------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------

def model_to_dict(obj):
    if obj is None:
        return None

    return {
        c.name: getattr(obj, c.name)
        for c in obj.__table__.columns
    }


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def is_valid_name(name: str) -> bool:
    name_clean = name.strip()
    name_lower = name_clean.lower()

    if len(name_clean) < 2 or len(name_clean) > 40:
        return False

    invalid_phrases = [
        "yes", "no", "yeah", "nope", "mistake", "wait", "ok",
        "cancel", "tell me about yourself", "who are you",
        "what do you do", "hi", "hello", "hey", "help"
    ]

    if name_lower in invalid_phrases:
        return False

    words = name_clean.split()

    if len(words) > 4:
        return False

    forbidden_words = [
        "tell", "about", "yourself", "what", "who", "how",
        "why", "where", "can", "do"
    ]

    if any(word in name_lower for word in forbidden_words) and len(words) > 1:
        return False

    if any(char.isdigit() for char in name_clean):
        return False

    return True


def is_valid_datetime(dt_str: str) -> bool:
    dt_clean = dt_str.strip().lower()

    invalid_words = ["no", "cancel", "stop", "nope", "skip", "none"]

    if dt_clean in invalid_words or len(dt_clean) < 3:
        return False

    time_keywords = [
        "tomorrow", "today", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday", "am", "pm",
        "morning", "afternoon", "evening", "night", "now", "soon", "at", ":"
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


def get_business_settings(db):
    settings = db.query(AvaBusinessSetting).first()

    if settings:
        return settings

    # Safe defaults if the settings row has not been created.
    class DefaultSettings:
        timezone = "Asia/Kolkata"
        appointment_duration_minutes = 60
        booking_window_days = 7

    return DefaultSettings()


def get_local_now(settings):
    timezone_name = settings.timezone or "Asia/Kolkata"

    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone = ZoneInfo("Asia/Kolkata")

    return datetime.now(timezone)


def get_working_hour(db, selected_date: date):
    return (
        db.query(AvaBusinessWorkingHour)
        .filter(
            AvaBusinessWorkingHour.day_of_week == selected_date.weekday()
        )
        .first()
    )


def get_blocking_appointments(db, selected_date: date):
    start_of_day = datetime.combine(selected_date, time.min)
    end_of_day = datetime.combine(
        selected_date + timedelta(days=1),
        time.min
    )

    return (
        db.query(AvaAppointment)
        .filter(
            AvaAppointment.appointment_date >= start_of_day,
            AvaAppointment.appointment_date < end_of_day,
            AvaAppointment.status.in_(["pending", "confirmed"])
        )
        .all()
    )


def is_slot_available(
    db,
    selected_date: date,
    selected_time: time,
    duration_minutes: int,
    local_now: datetime
):
    working_hour = get_working_hour(db, selected_date)

    if not working_hour or not working_hour.is_open:
        return False

    if not working_hour.opening_time or not working_hour.closing_time:
        return False

    slot_start = datetime.combine(selected_date, selected_time)
    slot_end = slot_start + timedelta(minutes=duration_minutes)

    opening = datetime.combine(selected_date, working_hour.opening_time)
    closing = datetime.combine(selected_date, working_hour.closing_time)

    if slot_start < opening or slot_end > closing:
        return False

    # Appointment DateTime values in the database are naive local times.
    local_now_naive = local_now.replace(tzinfo=None)

    if slot_start <= local_now_naive:
        return False

    appointments = get_blocking_appointments(db, selected_date)

    for appointment in appointments:
        existing_start = appointment.appointment_date
        existing_end = existing_start + timedelta(
            minutes=appointment.duration_minutes
        )

        # Check overlapping appointment times.
        if slot_start < existing_end and slot_end > existing_start:
            return False

    return True


def get_available_dates(db, settings, local_now):
    booking_window = max(1, int(settings.booking_window_days or 7))

    dates = []

    for day_offset in range(booking_window):
        selected_date = local_now.date() + timedelta(days=day_offset)
        working_hour = get_working_hour(db, selected_date)

        is_open = bool(
            working_hour
            and working_hour.is_open
            and working_hour.opening_time
            and working_hour.closing_time
        )

        dates.append({
            "date": selected_date.isoformat(),
            "label": selected_date.strftime("%d %b %Y"),
            "day": selected_date.strftime("%A"),
            "is_open": is_open,
            "disabled": not is_open
        })

    return dates


def get_available_slots(db, settings, selected_date, local_now):
    working_hour = get_working_hour(db, selected_date)

    if (
        not working_hour
        or not working_hour.is_open
        or not working_hour.opening_time
        or not working_hour.closing_time
    ):
        return []

    duration = max(
        1,
        int(settings.appointment_duration_minutes or 60)
    )

    slots = []

    current_time = datetime.combine(
        selected_date,
        working_hour.opening_time
    )

    closing_time = datetime.combine(
        selected_date,
        working_hour.closing_time
    )

    while current_time + timedelta(minutes=duration) <= closing_time:
        slot_time = current_time.time()

        available = is_slot_available(
            db=db,
            selected_date=selected_date,
            selected_time=slot_time,
            duration_minutes=duration,
            local_now=local_now
        )

        slots.append({
            "time": slot_time.strftime("%H:%M"),
            "label": current_time.strftime("%I:%M %p"),
            "available": available,
            "disabled": not available
        })

        current_time += timedelta(minutes=duration)

    return slots


def save_chat_messages(db, conversation, user_message, reply):
    if user_message:
        db.add(
            AvaMessage(
                conversation_id=conversation.id,
                sender="user",
                message=user_message
            )
        )

    db.add(
        AvaMessage(
            conversation_id=conversation.id,
            sender="ava",
            message=reply
        )
    )


def chat_response(
    reply,
    session_id,
    ui_action=None,
    data=None
):
    return {
        "reply": reply,
        "session_id": session_id,
        "ui_action": ui_action,
        "data": data
    }


# ---------------------------------------------------------
# REQUEST / RESPONSE
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = ""
    session_id: str | None = None
    action: str | None = None
    selected_date: date | None = None
    selected_time: time | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None
    ui_action: str | None = None
    data: dict | None = None


# ---------------------------------------------------------
# FAQ MATCHING
# ---------------------------------------------------------

def match_faq(db, user_message: str, detected_intent: str):
    faqs = (
        db.query(AvaBusinessFAQ)
        .filter(AvaBusinessFAQ.is_active == True)
        .all()
    )

    if not faqs:
        return None

    faq_questions = [faq.question for faq in faqs]
    corpus = faq_questions + [user_message]

    log_debug_data(
        "Step 1: FAQ Corpus for TF-IDF",
        {
            "corpus": corpus,
            "detected_intent": detected_intent
        },
        type="chat_faq"
    )

    try:
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)

        faq_vectors = tfidf_matrix[:-1]
        user_vector = tfidf_matrix[-1]

        similarities = cosine_similarity(
            user_vector,
            faq_vectors
        ).flatten()

        best_match_idx = similarities.argmax()
        best_score = similarities[best_match_idx]

        if best_score >= 0.20:
            return faqs[best_match_idx].answer

    except ValueError:
        return None

    return None


# ---------------------------------------------------------
# MAIN CHAT ENDPOINT
# ---------------------------------------------------------

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    message = request.message.strip()

    log_debug_data(
        "Step 1: User Message Received",
        {
            "message": message,
            "session_id": request.session_id,
            "action": request.action
        }
    )

    # Validate action-only requests before opening DB.
    if not message:
        if request.action not in ["select_date", "select_time"]:
            return chat_response(
                "Please enter a message.",
                request.session_id
            )

        if request.action == "select_date" and not request.selected_date:
            return chat_response(
                "Please select a valid date.",
                request.session_id
            )

        if request.action == "select_time" and (
            not request.selected_date or not request.selected_time
        ):
            return chat_response(
                "Please select a valid date and time.",
                request.session_id
            )

    session_id = request.session_id or str(uuid.uuid4())

    db = SessionLocal()

    try:
        conversation = get_or_create_conversation(db, session_id)

        current_step = conversation.current_step

        lead_data = (
            json.loads(conversation.lead_data)
            if conversation.lead_data else {}
        )

        settings = get_business_settings(db)
        local_now = get_local_now(settings)

        reply = ""
        ui_action = None
        response_data = None

        # -------------------------------------------------
        # APPOINTMENT DATE ACTION
        # -------------------------------------------------

        if request.action == "select_date":

            if current_step != "booking_selecting_date":
                return chat_response(
                    "Please follow the appointment booking steps.",
                    session_id
                )

            selected_date = request.selected_date

            available_dates = get_available_dates(
                db,
                settings,
                local_now
            )

            allowed_dates = [
                item["date"]
                for item in available_dates
                if item["is_open"]
            ]

            if selected_date.isoformat() not in allowed_dates:
                reply = (
                    "That date is not available. "
                    "Please choose one of the available dates."
                )

                ui_action = "select_date"
                response_data = {"dates": available_dates}

            else:
                slots = get_available_slots(
                    db,
                    settings,
                    selected_date,
                    local_now
                )

                if not any(slot["available"] for slot in slots):
                    reply = (
                        "Sorry, there are no available appointments "
                        "on that date. Please select another date."
                    )

                    ui_action = "select_date"
                    response_data = {"dates": available_dates}

                else:
                    lead_data["appointment_date"] = selected_date.isoformat()

                    conversation.lead_data = json.dumps(lead_data)
                    conversation.current_step = "booking_selecting_time"

                    reply = (
                        f"Great! Here are the available appointment "
                        f"times for {selected_date.strftime('%d %b %Y')}. "
                        "Please select a time."
                    )

                    ui_action = "select_time"
                    response_data = {
                        "date": selected_date.isoformat(),
                        "slots": slots
                    }

        # -------------------------------------------------
        # APPOINTMENT TIME ACTION
        # -------------------------------------------------

        elif request.action == "select_time":

            if current_step != "booking_selecting_time":
                return chat_response(
                    "Please follow the appointment booking steps.",
                    session_id
                )

            selected_date = request.selected_date
            selected_time = request.selected_time

            saved_date = lead_data.get("appointment_date")

            if (
                not saved_date
                or saved_date != selected_date.isoformat()
            ):
                return chat_response(
                    "Your selected date does not match the booking. "
                    "Please select the date again.",
                    session_id,
                    "select_date",
                    {
                        "dates": get_available_dates(
                            db,
                            settings,
                            local_now
                        )
                    }
                )

            duration = max(
                1,
                int(settings.appointment_duration_minutes or 60)
            )

            available = is_slot_available(
                db=db,
                selected_date=selected_date,
                selected_time=selected_time,
                duration_minutes=duration,
                local_now=local_now
            )

            if not available:
                slots = get_available_slots(
                    db,
                    settings,
                    selected_date,
                    local_now
                )

                reply = (
                    "Sorry, that time slot is no longer available. "
                    "Please select another available time."
                )

                ui_action = "select_time"
                response_data = {
                    "date": selected_date.isoformat(),
                    "slots": slots
                }

            else:
                appointment_datetime = datetime.combine(
                    selected_date,
                    selected_time
                )

                new_appointment = AvaAppointment(
                    name=lead_data["name"],
                    phone=lead_data["phone"],
                    email=None,
                    service=lead_data["service"],
                    appointment_date=appointment_datetime,
                    duration_minutes=duration,
                    status="pending",
                    source="website_chat"
                )

                db.add(new_appointment)

                conversation.current_step = None
                conversation.intent = None
                conversation.lead_data = json.dumps({})

                reply = (
                    f"Your appointment request has been successfully "
                    f"submitted, {lead_data['name']}!\n\n"
                    f"Service: {lead_data['service']}\n"
                    f"Date: {selected_date.strftime('%d %b %Y')}\n"
                    f"Time: {selected_time.strftime('%I:%M %p')}\n\n"
                    "Your appointment is currently pending confirmation. "
                    "Our team will contact you if any further confirmation "
                    "is required."
                )

        # -------------------------------------------------
        # NORMAL MESSAGE PROCESSING
        # -------------------------------------------------

        else:

            # Only run the ML classifier when there is a message.
            if message:
                X = vectorizer.transform([message])
                intent = str(model.predict(X)[0])
            else:
                intent = conversation.intent or ""

            msg_lower = message.lower()

            # Keyword overrides
            if message:
                if any(
                    kw in msg_lower
                    for kw in [
                        "price", "pricing", "cost", "charge",
                        "charges", "rate", "rates"
                    ]
                ):
                    intent = "pricing"

                elif any(
                    kw in msg_lower
                    for kw in [
                        "service", "services", "offer",
                        "do you do", "build"
                    ]
                ):
                    intent = "services"

                elif any(
                    kw in msg_lower
                    for kw in [
                        "hour", "hours", "open", "close", "weekend"
                    ]
                ):
                    intent = "business_hours"

                elif any(
                    kw in msg_lower
                    for kw in [
                        "contact", "email", "phone", "reach", "call"
                    ]
                ):
                    intent = "contact"

            conversation.intent = intent

            log_debug_data(
                "Step 2: Intent Detected",
                {"intent": intent}
            )

            # ---------------------------------------------
            # EXISTING GENERAL LEAD WORKFLOW
            # ---------------------------------------------

            if current_step == "collecting_name":

                if not is_valid_name(message):
                    reply = (
                        "That doesn't look like a valid name. "
                        "Could you please provide your full name?"
                    )
                else:
                    lead_data["name"] = message
                    conversation.lead_data = json.dumps(lead_data)
                    conversation.current_step = "collecting_phone"

                    reply = (
                        f"Thanks, {message}! Now, could you please "
                        "provide your phone number?"
                    )

            elif current_step == "collecting_phone":

                if not is_valid_phone(message):
                    reply = (
                        "That doesn't look like a valid phone number. "
                        "Please enter a valid 10-digit phone number "
                        "so we can reach you."
                    )
                else:
                    lead_data["phone"] = message
                    conversation.lead_data = json.dumps(lead_data)
                    conversation.current_step = "collecting_service"

                    reply = "Great! What service are you interested in?"

            elif current_step == "collecting_service":

                lead_data["requested_service"] = message
                conversation.lead_data = json.dumps(lead_data)
                conversation.current_step = "collecting_datetime"

                reply = (
                    "When would you prefer to schedule this consultation? "
                    "(e.g., Tomorrow at 2 PM)"
                )

            elif current_step == "collecting_datetime":

                if not is_valid_datetime(message):
                    reply = (
                        "Please provide a preferred date or time "
                        "(e.g., 'Tomorrow at 2 PM' or 'Monday morning') "
                        "so we can schedule your appointment."
                    )
                else:
                    lead_data["preferred_datetime"] = message
                    conversation.lead_data = json.dumps(lead_data)

                    new_lead = AvaLead(
                        name=lead_data.get("name", "Valued Customer"),
                        phone=lead_data.get("phone", ""),
                        requested_service=lead_data.get(
                            "requested_service",
                            "General Inquiry"
                        ),
                        preferred_datetime=lead_data.get(
                            "preferred_datetime",
                            ""
                        ),
                        status="new",
                        source="website_chat"
                    )

                    db.add(new_lead)

                    conversation.current_step = None
                    conversation.intent = None
                    conversation.lead_data = json.dumps({})

                    reply = (
                        f"You're all set, {new_lead.name}! "
                        "I've successfully saved your request. "
                        "Our team will contact you shortly."
                    )

            # ---------------------------------------------
            # APPOINTMENT BOOKING WORKFLOW
            # ---------------------------------------------

            elif current_step == "booking_collecting_name":

                if not is_valid_name(message):
                    reply = (
                        "That doesn't look like a valid name. "
                        "Could you please provide your full name?"
                    )
                else:
                    lead_data["name"] = message
                    conversation.lead_data = json.dumps(lead_data)
                    conversation.current_step = "booking_collecting_phone"

                    reply = (
                        f"Thanks, {message}! "
                        "Now, could you please provide your phone number?"
                    )

            elif current_step == "booking_collecting_phone":

                if not is_valid_phone(message):
                    reply = (
                        "That doesn't look like a valid phone number. "
                        "Please enter a valid phone number."
                    )
                else:
                    lead_data["phone"] = message
                    conversation.lead_data = json.dumps(lead_data)
                    conversation.current_step = "booking_collecting_service"

                    reply = "Great! Which service would you like to book?"

            elif current_step == "booking_collecting_service":

                if len(message) < 2 or len(message) > 255:
                    reply = "Please enter a valid service name."
                else:
                    lead_data["service"] = message
                    conversation.lead_data = json.dumps(lead_data)

                    dates = get_available_dates(
                        db,
                        settings,
                        local_now
                    )

                    if not any(item["is_open"] for item in dates):
                        reply = (
                            "Sorry, there are no appointment dates "
                            "available in the current booking window."
                        )
                        conversation.current_step = None
                        conversation.lead_data = json.dumps({})
                    else:
                        conversation.current_step = "booking_selecting_date"

                        reply = (
                            "Thank you! Please select an appointment date "
                            "from the available dates below."
                        )

                        ui_action = "select_date"
                        response_data = {"dates": dates}

            # ---------------------------------------------
            # START NEW APPOINTMENT
            # ---------------------------------------------

            elif (
                intent == "appointment"
                or any(
                    kw in msg_lower
                    for kw in [
                        "appointment", "schedule", "book", "meeting"
                    ]
                )
            ):
                conversation.current_step = "booking_collecting_name"
                conversation.lead_data = json.dumps({})

                reply = (
                    "I would love to help you schedule an appointment! "
                    "To get started, what is your full name?"
                )

            # ---------------------------------------------
            # FAQ / NORMAL CHAT
            # ---------------------------------------------

            else:
                faq_answer = match_faq(db, message, intent)

                log_debug_data(
                    "Step 3: FAQ Matching Result",
                    {
                        "faq_answer": faq_answer,
                        "intent": intent
                    }
                )

                if faq_answer:
                    reply = faq_answer

                elif intent == "greeting":
                    reply = (
                        "Hello! Welcome to WebeXcellence. "
                        "How can I help you today? Would you like "
                        "to explore our services or book an appointment?"
                    )

                elif intent == "goodbye":
                    reply = (
                        "Goodbye! Feel free to reach out if you have "
                        "any more questions. Have a great day!"
                    )

                elif intent == "human_escalation":
                    reply = (
                        "I can definitely connect you with a member "
                        "of our team. Would you like to schedule a "
                        "callback or leave your contact details?"
                    )

                else:
                    reply = (
                        "I'd be happy to help you with that. "
                        "Would you like to schedule a consultation "
                        "or check out our services?"
                    )

        # -------------------------------------------------
        # SAVE MESSAGES AND COMMIT
        # -------------------------------------------------

        save_chat_messages(
            db,
            conversation,
            message,
            reply
        )

        db.commit()

        log_debug_data(
            "Chat Processing Completed",
            {
                "conversation_id": conversation.id,
                "current_step": conversation.current_step,
                "ui_action": ui_action,
                "data": response_data
            }
        )

        return chat_response(
            reply,
            session_id,
            ui_action,
            response_data
        )

    except Exception as exc:
        db.rollback()

        log_debug_data(
            "Chat Processing Error",
            {"error": str(exc)}
        )

        raise

    finally:
        db.close()