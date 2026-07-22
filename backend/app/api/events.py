import re
from datetime import datetime, time, timedelta, timezone
from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Event, EventStatus, UserRole

events_bp = Blueprint("events", __name__)


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                return {"message": "You do not have permission to do that."}, 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def unique_slug(title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "event"
    slug = base
    suffix = 2
    while Event.query.filter_by(slug=slug).first():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def parse_event_payload(data):
    required = ("title", "description", "venue", "county", "startsAt", "category", "ticketPriceCents", "ticketCapacity")
    if any(data.get(field) in (None, "") for field in required):
        raise ValueError("Complete every required event field.")
    starts_at = datetime.fromisoformat(str(data["startsAt"]).replace("Z", "+00:00"))
    price = int(data["ticketPriceCents"])
    capacity = int(data["ticketCapacity"])
    if price < 0 or capacity < 1:
        raise ValueError("Ticket price and capacity must be valid.")
    return {
        "title": str(data["title"]).strip(),
        "description": str(data["description"]).strip(),
        "venue": str(data["venue"]).strip(),
        "county": str(data["county"]).strip(),
        "starts_at": starts_at,
        "category": str(data["category"]).strip(),
        "ticket_price_cents": price,
        "ticket_capacity": capacity,
    }


def date_window(value):
    """Return an inclusive UTC window for common Ireland event filters."""
    local_tz = ZoneInfo("Europe/Dublin")
    now = datetime.now(local_tz)
    today = now.date()

    if value == "today":
        start_day = end_day = today
    elif value == "tomorrow":
        start_day = end_day = today + timedelta(days=1)
    elif value == "this-weekend":
        days_until_saturday = (5 - today.weekday()) % 7
        start_day = today + timedelta(days=days_until_saturday)
        end_day = start_day + timedelta(days=1)
    elif value == "next-week":
        start_day = today + timedelta(days=(7 - today.weekday()))
        end_day = start_day + timedelta(days=6)
    elif value == "this-week":
        start_day = today
        end_day = today + timedelta(days=(6 - today.weekday()))
    else:
        return None

    start = datetime.combine(start_day, time.min, tzinfo=local_tz).astimezone(timezone.utc)
    end = datetime.combine(end_day, time.max, tzinfo=local_tz).astimezone(timezone.utc)
    return start, end


@events_bp.get("")
def list_events():
    query = Event.query.filter_by(status=EventStatus.APPROVED)
    search = request.args.get("q", "").strip()
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Event.title.ilike(term), Event.description.ilike(term), Event.venue.ilike(term)))
    if request.args.get("category"):
        query = query.filter_by(category=request.args["category"])
    if request.args.get("county"):
        query = query.filter_by(county=request.args["county"])
    window = date_window(request.args.get("date"))
    if window:
        query = query.filter(Event.starts_at.between(*window))
    if request.args.get("minPrice"):
        query = query.filter(Event.ticket_price_cents >= int(float(request.args["minPrice"]) * 100))
    if request.args.get("maxPrice"):
        query = query.filter(Event.ticket_price_cents <= int(float(request.args["maxPrice"]) * 100))
    if request.args.get("free") == "true":
        query = query.filter(Event.ticket_price_cents == 0)
    sort = request.args.get("sort", "date")
    if sort == "price-low":
        query = query.order_by(Event.ticket_price_cents.asc(), Event.starts_at.asc())
    elif sort == "price-high":
        query = query.order_by(Event.ticket_price_cents.desc(), Event.starts_at.asc())
    else:
        query = query.order_by(Event.starts_at.asc())
    events = query.all()
    return {"events": [event.to_dict() for event in events]}


@events_bp.get("/<slug>")
def event_detail(slug):
    event = Event.query.filter_by(slug=slug, status=EventStatus.APPROVED).first_or_404()
    return {"event": event.to_dict()}


@events_bp.post("")
@login_required
def create_event():
    try:
        fields = parse_event_payload(request.get_json(silent=True) or {})
    except (TypeError, ValueError) as exc:
        return {"message": str(exc)}, 400

    if current_user.role == UserRole.ATTENDEE:
        current_user.role = UserRole.ORGANISER
    event = Event(
        **fields,
        slug=unique_slug(fields["title"]),
        organiser=current_user,
        status=EventStatus.PENDING,
    )
    db.session.add(event)
    db.session.commit()
    return {"event": event.to_dict(include_private=True)}, 201


@events_bp.get("/mine/list")
@login_required
def my_events():
    events = Event.query.filter_by(organiser_id=current_user.id).order_by(Event.created_at.desc()).all()
    return {"events": [event.to_dict(include_private=True) for event in events]}


@events_bp.put("/<int:event_id>")
@login_required
def update_event(event_id):
    event = db.get_or_404(Event, event_id)
    if event.organiser_id != current_user.id and current_user.role != UserRole.ADMIN:
        return {"message": "You do not have permission to edit this event."}, 403
    if event.status == EventStatus.APPROVED and current_user.role != UserRole.ADMIN:
        return {"message": "Contact EventSpace before editing a live event."}, 409
    try:
        fields = parse_event_payload(request.get_json(silent=True) or {})
    except (TypeError, ValueError) as exc:
        return {"message": str(exc)}, 400
    for field, value in fields.items():
        setattr(event, field, value)
    event.status = EventStatus.PENDING
    event.rejection_reason = None
    db.session.commit()
    return {"event": event.to_dict(include_private=True)}


@events_bp.get("/admin/pending")
@role_required(UserRole.ADMIN)
def pending_events():
    events = Event.query.filter_by(status=EventStatus.PENDING).order_by(Event.created_at.asc()).all()
    return {"events": [event.to_dict(include_private=True) for event in events]}


@events_bp.get("/admin/overview")
@role_required(UserRole.ADMIN)
def admin_overview():
    events = Event.query.order_by(Event.created_at.desc()).all()
    counts = {
        status.value: Event.query.filter_by(status=status).count()
        for status in EventStatus
    }
    return {
        "counts": counts,
        "events": [event.to_dict(include_private=True) for event in events],
    }


@events_bp.post("/<int:event_id>/decision")
@role_required(UserRole.ADMIN)
def decide_event(event_id):
    event = db.get_or_404(Event, event_id)
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    if decision not in ("approved", "rejected"):
        return {"message": "Decision must be approved or rejected."}, 400
    event.status = EventStatus(decision)
    event.rejection_reason = str(data.get("reason", "")).strip() if decision == "rejected" else None
    db.session.commit()
    return {"event": event.to_dict(include_private=True)}
