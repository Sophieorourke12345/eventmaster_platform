import enum
import secrets
from datetime import datetime, timedelta, timezone

from flask_login import UserMixin

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class UserRole(enum.Enum):
    ATTENDEE = "attendee"
    ORGANISER = "organiser"
    ADMIN = "admin"


class EventStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.ATTENDEE)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    stripe_account_id = db.Column(db.String(255), unique=True)
    stripe_charges_enabled = db.Column(db.Boolean, nullable=False, default=False)
    stripe_payouts_enabled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    events = db.relationship("Event", back_populates="organiser", lazy="dynamic")
    orders = db.relationship("Order", back_populates="buyer", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "role": self.role.value,
            "emailVerified": self.email_verified,
            "stripeAccountCreated": bool(self.stripe_account_id),
            "stripeOnboarded": self.stripe_charges_enabled and self.stripe_payouts_enabled,
        }


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    county = db.Column(db.String(80), nullable=False, index=True)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    ticket_price_cents = db.Column(db.Integer, nullable=False)
    ticket_capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(EventStatus), nullable=False, default=EventStatus.DRAFT, index=True)
    rejection_reason = db.Column(db.Text)
    organiser_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    organiser = db.relationship("User", back_populates="events")
    images = db.relationship("EventImage", back_populates="event", cascade="all, delete-orphan", order_by="EventImage.position")
    tickets = db.relationship("Ticket", back_populates="event", lazy="dynamic")
    orders = db.relationship("Order", back_populates="event", lazy="dynamic")

    @property
    def tickets_sold(self):
        return self.tickets.count()

    @property
    def tickets_remaining(self):
        reserved = self.orders.filter(
            Order.status == OrderStatus.PENDING,
            Order.expires_at > utc_now(),
        ).with_entities(db.func.coalesce(db.func.sum(Order.quantity), 0)).scalar()
        return max(self.ticket_capacity - self.tickets_sold - int(reserved or 0), 0)

    @property
    def is_expired(self):
        starts_at = self.starts_at
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        return starts_at < utc_now() - timedelta(days=1)

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "venue": self.venue,
            "county": self.county,
            "startsAt": self.starts_at.isoformat(),
            "category": self.category,
            "ticketPriceCents": self.ticket_price_cents,
            "ticketCapacity": self.ticket_capacity,
            "ticketsRemaining": self.tickets_remaining,
            "ticketsSold": self.tickets_sold,
            "soldOut": self.tickets_remaining == 0,
            "expired": self.is_expired,
            "status": self.status.value,
            "images": [image.to_dict() for image in self.images],
            "organiser": {"id": self.organiser.id, "name": self.organiser.full_name},
        }
        if include_private:
            data["rejectionReason"] = self.rejection_reason
        return data


class EventImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(255), nullable=False, default="Event image")
    position = db.Column(db.Integer, nullable=False, default=0)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)

    event = db.relationship("Event", back_populates="images")

    def to_dict(self):
        return {"id": self.id, "url": f"/uploads/{self.filename}", "alt": self.alt_text}


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    platform_fee_cents = db.Column(db.Integer, nullable=False)
    stripe_checkout_session_id = db.Column(db.String(255), unique=True)
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    buyer = db.relationship("User", back_populates="orders")
    event = db.relationship("Event", back_populates="orders")
    tickets = db.relationship("Ticket", back_populates="order", cascade="all, delete-orphan")


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    verification_code = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(24))
    checked_in_at = db.Column(db.DateTime(timezone=True))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)

    event = db.relationship("Event", back_populates="tickets")
    order = db.relationship("Order", back_populates="tickets")
