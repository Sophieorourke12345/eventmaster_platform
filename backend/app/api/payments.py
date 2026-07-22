from datetime import timedelta

import stripe
from flask import Blueprint, current_app, request
from flask_login import current_user, login_required

from ..extensions import db
from ..extensions import csrf
from ..models import Event, EventStatus, Order, OrderStatus, Ticket, User, utc_now

payments_bp = Blueprint("payments", __name__)


def configure_stripe():
    secret = current_app.config["STRIPE_SECRET_KEY"]
    if not secret:
        return False
    stripe.api_key = secret
    return True


def refresh_connected_account(user):
    if not user.stripe_account_id or not configure_stripe():
        return
    account = stripe.Account.retrieve(user.stripe_account_id)
    user.stripe_charges_enabled = bool(account.charges_enabled)
    user.stripe_payouts_enabled = bool(account.payouts_enabled)
    db.session.commit()


@payments_bp.post("/connect/onboard")
@login_required
def connect_onboard():
    if not configure_stripe():
        return {"message": "Stripe test mode is not configured yet."}, 503

    if not current_user.stripe_account_id:
        account = stripe.Account.create(
            type="express",
            country="IE",
            email=current_user.email,
            capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
            metadata={"eventspace_user_id": str(current_user.id)},
        )
        current_user.stripe_account_id = account.id
        db.session.commit()

    frontend = current_app.config["FRONTEND_URL"].rstrip("/")
    link = stripe.AccountLink.create(
        account=current_user.stripe_account_id,
        refresh_url=f"{frontend}/organiser?stripe=refresh",
        return_url=f"{frontend}/organiser?stripe=return",
        type="account_onboarding",
    )
    return {"url": link.url}


@payments_bp.get("/connect/status")
@login_required
def connect_status():
    try:
        refresh_connected_account(current_user)
    except stripe.StripeError:
        return {"message": "Stripe account status is temporarily unavailable."}, 502
    return {
        "accountCreated": bool(current_user.stripe_account_id),
        "chargesEnabled": current_user.stripe_charges_enabled,
        "payoutsEnabled": current_user.stripe_payouts_enabled,
        "onboarded": current_user.stripe_charges_enabled and current_user.stripe_payouts_enabled,
    }


@payments_bp.post("/checkout")
@login_required
def create_checkout():
    if not configure_stripe():
        return {"message": "Stripe test mode is not configured yet."}, 503
    data = request.get_json(silent=True) or {}
    try:
        event_id = int(data.get("eventId"))
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return {"message": "Choose a valid ticket quantity."}, 400
    if quantity < 1 or quantity > 10:
        return {"message": "You can purchase between 1 and 10 tickets."}, 400

    event = db.get_or_404(Event, event_id)
    if event.status != EventStatus.APPROVED:
        return {"message": "This event is not currently on sale."}, 409
    if event.organiser_id == current_user.id:
        return {"message": "Organisers cannot buy tickets for their own event."}, 409
    if quantity > event.tickets_remaining:
        return {"message": "There are not enough tickets remaining."}, 409
    refresh_connected_account(event.organiser)
    if not event.organiser.stripe_charges_enabled:
        return {"message": "Ticket sales will open when the organiser finishes payout verification."}, 409

    total_cents = event.ticket_price_cents * quantity
    fee_percent = current_app.config["STRIPE_PLATFORM_FEE_PERCENT"]
    platform_fee_cents = (total_cents * fee_percent + 50) // 100
    expires_at = utc_now() + timedelta(minutes=30)
    order = Order(
        buyer=current_user,
        event=event,
        quantity=quantity,
        total_cents=total_cents,
        platform_fee_cents=platform_fee_cents,
        status=OrderStatus.PENDING,
        expires_at=expires_at,
    )
    db.session.add(order)
    db.session.flush()

    frontend = current_app.config["FRONTEND_URL"].rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=current_user.email,
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": event.ticket_price_cents,
                    "product_data": {"name": event.title, "description": f"{event.venue}, {event.county}"},
                },
                "quantity": quantity,
            }],
            payment_intent_data={
                "application_fee_amount": platform_fee_cents,
                "transfer_data": {"destination": event.organiser.stripe_account_id},
                "on_behalf_of": event.organiser.stripe_account_id,
                "metadata": {"eventspace_order_id": str(order.id)},
            },
            metadata={"eventspace_order_id": str(order.id)},
            success_url=f"{frontend}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend}/events/{event.slug}?checkout=cancelled",
            expires_at=int(expires_at.timestamp()),
        )
    except stripe.StripeError:
        db.session.rollback()
        return {"message": "Stripe could not start checkout. Please try again."}, 502

    order.stripe_checkout_session_id = session.id
    db.session.commit()
    return {"url": session.url}


@payments_bp.get("/tickets")
@login_required
def my_tickets():
    tickets = (
        Ticket.query.join(Order)
        .filter(Order.buyer_id == current_user.id, Order.status == OrderStatus.PAID)
        .order_by(Ticket.id.desc()).all()
    )
    return {"tickets": [{
        "id": ticket.id,
        "verificationCode": ticket.verification_code,
        "checkedInAt": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
        "event": ticket.event.to_dict(),
    } for ticket in tickets]}


@payments_bp.post("/webhook")
@csrf.exempt
def stripe_webhook():
    secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    if not secret:
        return {"message": "Stripe webhook is not configured."}, 503
    try:
        event = stripe.Webhook.construct_event(request.get_data(), request.headers.get("Stripe-Signature"), secret)
    except (ValueError, stripe.SignatureVerificationError):
        return {"message": "Invalid webhook signature."}, 400

    stripe_object = event["data"]["object"]
    if event["type"] == "checkout.session.completed" and stripe_object.get("payment_status") == "paid":
        order = Order.query.filter_by(stripe_checkout_session_id=stripe_object["id"]).first()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            order.stripe_payment_intent_id = stripe_object.get("payment_intent")
            for _ in range(order.quantity):
                db.session.add(Ticket(event=order.event, order=order))
            db.session.commit()
    elif event["type"] == "checkout.session.expired":
        order = Order.query.filter_by(stripe_checkout_session_id=stripe_object["id"]).first()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.FAILED
            db.session.commit()
    elif event["type"] == "account.updated":
        user = User.query.filter_by(stripe_account_id=stripe_object["id"]).first()
        if user:
            user.stripe_charges_enabled = bool(stripe_object.get("charges_enabled"))
            user.stripe_payouts_enabled = bool(stripe_object.get("payouts_enabled"))
            db.session.commit()
    return {"received": True}
