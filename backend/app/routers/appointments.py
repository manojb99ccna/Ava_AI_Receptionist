
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import (
    AvaAppointment,
    AvaBusinessSetting,
    AvaBusinessWorkingHour
)

# Admin appointment APIs
router = APIRouter(
    prefix="/admin/appointments",
    tags=["Appointments"]
)

 
# --------------------------------------------------
# ADMIN: GET ALL APPOINTMENTS
# --------------------------------------------------

@router.get("/")
def get_appointments(db: Session = Depends(get_db)):

    appointments = (
        db.query(AvaAppointment)
        .order_by(AvaAppointment.appointment_date.asc())
        .all()
    )

    return appointments


# --------------------------------------------------
# ADMIN: GET APPOINTMENTS BY DATE
# --------------------------------------------------

@router.get("/by-date")
def get_appointments_by_date(
    appointment_date: date = Query(...),
    db: Session = Depends(get_db)
):

    start_datetime = datetime.combine(
        appointment_date,
        time.min
    )

    end_datetime = start_datetime + timedelta(days=1)

    appointments = (
        db.query(AvaAppointment)
        .filter(
            AvaAppointment.appointment_date >= start_datetime,
            AvaAppointment.appointment_date < end_datetime
        )
        .order_by(AvaAppointment.appointment_date.asc())
        .all()
    )

    return appointments


# --------------------------------------------------
# CUSTOMER: GET AVAILABLE DATES (NEXT 7 DAYS)
# --------------------------------------------------

@router.get("/available-dates")
def get_available_dates(
    db: Session = Depends(get_db)
):

    # Get general appointment settings
    settings = db.query(AvaBusinessSetting).first()

    if not settings:
        raise HTTPException(
            status_code=500,
            detail="Appointment settings not configured"
        )

    # Validate settings
    if settings.booking_window_days <= 0:
        raise HTTPException(
            status_code=500,
            detail="Invalid booking window configuration"
        )

    if settings.appointment_duration_minutes <= 0:
        raise HTTPException(
            status_code=500,
            detail="Invalid appointment duration configuration"
        )

    # Business timezone
    try:
        timezone = ZoneInfo(settings.timezone)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Invalid business timezone configuration"
        )

    now = datetime.now(timezone)
    today = now.date()
    current_time = now.replace(tzinfo=None)

    booking_days = settings.booking_window_days
    duration = settings.appointment_duration_minutes

    result = []

    # Generate dates
    for day_offset in range(booking_days):

        selected_date = today + timedelta(days=day_offset)

        # Get working hours for the selected weekday
        working_hour = (
            db.query(AvaBusinessWorkingHour)
            .filter(
                AvaBusinessWorkingHour.day_of_week
                == selected_date.weekday()
            )
            .first()
        )

        # Check whether business is closed
        if (
            not working_hour
            or not working_hour.is_open
            or not working_hour.opening_time
            or not working_hour.closing_time
        ):

            result.append({
                "date": selected_date.isoformat(),
                "is_open": False,
                "is_available": False,
                "available_slots_count": 0
            })

            continue

        # Validate working hours
        if working_hour.opening_time >= working_hour.closing_time:
            raise HTTPException(
                status_code=500,
                detail="Invalid business working hours configuration"
            )

        # Get existing appointments for this date
        day_start = datetime.combine(
            selected_date,
            time.min
        )

        day_end = day_start + timedelta(days=1)

        existing_appointments = (
            db.query(AvaAppointment)
            .filter(
                AvaAppointment.appointment_date >= day_start,
                AvaAppointment.appointment_date < day_end
            )
            .all()
        )

        # Pending and confirmed appointments block slots.
        # Cancelled appointments do not block slots.
        booked_appointments = [
            appointment
            for appointment in existing_appointments
            if (appointment.status or "").lower() != "cancelled"
        ]

        available_slots_count = 0

        # Generate one-hour (configured duration) slots
        slot_start = datetime.combine(
            selected_date,
            working_hour.opening_time
        )

        closing_datetime = datetime.combine(
            selected_date,
            working_hour.closing_time
        )

        while True:

            slot_end = slot_start + timedelta(minutes=duration)

            # Do not generate slots beyond closing time
            if slot_end > closing_datetime:
                break

            # Exclude past slots for today
            if selected_date == today and slot_start <= current_time:
                slot_start = slot_end
                continue

            # Check overlapping appointments
            is_booked = any(
                appointment.appointment_date < slot_end
                and (
                    appointment.appointment_date
                    + timedelta(
                        minutes=appointment.duration_minutes
                    )
                ) > slot_start
                for appointment in booked_appointments
            )

            if not is_booked:
                available_slots_count += 1

            slot_start = slot_end

        # Add date result
        result.append({
            "date": selected_date.isoformat(),
            "is_open": True,
            "is_available": available_slots_count > 0,
            "available_slots_count": available_slots_count
        })

    return {
        "timezone": settings.timezone,
        "booking_window_days": booking_days,
        "appointment_duration_minutes": duration,
        "dates": result
    }



# --------------------------------------------------
# CUSTOMER: GET AVAILABLE TIME SLOTS FOR SELECTED DATE
# --------------------------------------------------

@router.get("/available-slots")
def get_available_slots(
    selected_date: date = Query(...),
    db: Session = Depends(get_db)
):

    # Get appointment settings
    settings = db.query(AvaBusinessSetting).first()

    if not settings:
        raise HTTPException(
            status_code=500,
            detail="Appointment settings not configured"
        )

    timezone = ZoneInfo(settings.timezone)

    now = datetime.now(timezone)
    today = now.date()
    current_time = now.replace(tzinfo=None)

    booking_days = settings.booking_window_days
    duration = settings.appointment_duration_minutes

    # Validate selected date
    last_booking_date = today + timedelta(days=booking_days - 1)

    if selected_date < today or selected_date > last_booking_date:
        raise HTTPException(
            status_code=400,
            detail="Selected date is outside the booking window"
        )

    # Get working hours
    working_hour = (
        db.query(AvaBusinessWorkingHour)
        .filter(
            AvaBusinessWorkingHour.day_of_week
            == selected_date.weekday()
        )
        .first()
    )

    # Check closed day
    if (
        not working_hour
        or not working_hour.is_open
        or not working_hour.opening_time
        or not working_hour.closing_time
    ):
        return {
            "date": selected_date.isoformat(),
            "is_open": False,
            "slots": []
        }

    # Validate working hours
    if working_hour.opening_time >= working_hour.closing_time:
        raise HTTPException(
            status_code=500,
            detail="Invalid business working hours configuration"
        )

    # Get existing appointments for selected date
    day_start = datetime.combine(selected_date, time.min)
    day_end = day_start + timedelta(days=1)

    existing_appointments = (
        db.query(AvaAppointment)
        .filter(
            AvaAppointment.appointment_date >= day_start,
            AvaAppointment.appointment_date < day_end
        )
        .all()
    )

    # Cancelled appointments do not block slots
    booked_appointments = [
        appointment
        for appointment in existing_appointments
        if (appointment.status or "").lower() != "cancelled"
    ]

    slots = []

    slot_start = datetime.combine(
        selected_date,
        working_hour.opening_time
    )

    closing_datetime = datetime.combine(
        selected_date,
        working_hour.closing_time
    )

    while True:

        slot_end = slot_start + timedelta(minutes=duration)

        # Stop when slot exceeds closing time
        if slot_end > closing_datetime:
            break

        # Check whether slot is in the past
        is_past = (
            selected_date == today
            and slot_start <= current_time
        )

        # Check overlapping appointments
        is_booked = any(
            appointment.appointment_date < slot_end
            and (
                appointment.appointment_date
                + timedelta(
                    minutes=appointment.duration_minutes
                )
            ) > slot_start
            for appointment in booked_appointments
        )

        is_available = not is_past and not is_booked

        slots.append({
            "start_time": slot_start.strftime("%H:%M"),
            "end_time": slot_end.strftime("%H:%M"),
            "is_available": is_available
        })

        slot_start = slot_end

    return {
        "date": selected_date.isoformat(),
        "is_open": True,
        "appointment_duration_minutes": duration,
        "slots": slots
    }



class AppointmentBookingRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=7, max_length=30)
    email: str | None = None
    service: str = Field(..., min_length=2, max_length=255)
    appointment_date: date
    start_time: time



@router.post("/book")
def book_appointment(
    booking: AppointmentBookingRequest,
    db: Session = Depends(get_db)
):
    # 1. Get business settings
    settings = db.query(AvaBusinessSetting).first()

    if not settings:
        raise HTTPException(
            status_code=500,
            detail="Business settings not configured"
        )

    duration = settings.appointment_duration_minutes
    timezone = ZoneInfo(settings.timezone)

    # 2. Validate booking date
    today = datetime.now(timezone).date()

    if booking.appointment_date < today:
        raise HTTPException(
            status_code=400,
            detail="Cannot book an appointment in the past"
        )

    last_date = today + timedelta(days=settings.booking_window_days - 1)

    if booking.appointment_date > last_date:
        raise HTTPException(
            status_code=400,
            detail="Appointment date is outside the booking window"
        )

    # 3. Check business working hours
    working_hours = (
        db.query(AvaBusinessWorkingHour)
        .filter(
            AvaBusinessWorkingHour.day_of_week
            == booking.appointment_date.weekday()
        )
        .first()
    )

    if not working_hours or not working_hours.is_open:
        raise HTTPException(
            status_code=400,
            detail="Business is closed on this date"
        )

    if not working_hours.opening_time or not working_hours.closing_time:
        raise HTTPException(
            status_code=400,
            detail="Business working hours are not configured"
        )

    # 4. Validate selected time
    appointment_datetime = datetime.combine(
        booking.appointment_date,
        booking.start_time
    )

    appointment_end = appointment_datetime + timedelta(minutes=duration)

    opening_datetime = datetime.combine(
        booking.appointment_date,
        working_hours.opening_time
    )

    closing_datetime = datetime.combine(
        booking.appointment_date,
        working_hours.closing_time
    )

    if (
        appointment_datetime < opening_datetime
        or appointment_end > closing_datetime
    ):
        raise HTTPException(
            status_code=400,
            detail="Selected time is outside business hours"
        )

    if (
        appointment_datetime - opening_datetime
    ).total_seconds() % (duration * 60) != 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid appointment time slot"
        )

    if appointment_datetime <= datetime.now(timezone).replace(tzinfo=None):
        raise HTTPException(
            status_code=400,
            detail="Cannot book a past time slot"
        )

    # 5. Check existing appointments
    existing_appointments = (
        db.query(AvaAppointment)
        .filter(
            AvaAppointment.appointment_date < appointment_end,
            AvaAppointment.status != "cancelled"
        )
        .all()
    )

    for appointment in existing_appointments:
        existing_end = appointment.appointment_date + timedelta(
            minutes=appointment.duration_minutes
        )

        if existing_end > appointment_datetime:
            raise HTTPException(
                status_code=409,
                detail="This appointment slot is already booked"
            )

    # 6. Save appointment
    new_appointment = AvaAppointment(
        name=booking.name,
        phone=booking.phone,
        email=booking.email,
        service=booking.service,
        appointment_date=appointment_datetime,
        duration_minutes=duration,
        status="pending",
        source="website_chat"
    )

    try:
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to book appointment"
        )

    # 7. Return response
    return {
        "success": True,
        "message": "Appointment booked successfully",
        "appointment": {
            "id": new_appointment.id,
            "name": new_appointment.name,
            "phone": new_appointment.phone,
            "service": new_appointment.service,
            "appointment_date": new_appointment.appointment_date,
            "duration_minutes": new_appointment.duration_minutes,
            "status": new_appointment.status
        }
    }    