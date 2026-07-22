from datetime import timedelta

import stripe
from flask import Blueprint, current_app, request
from flask_login import current_user, login_required

from ..extensions import db
from ..extensions import csrf
from ..models import Event, EventStatus, Order, OrderStatus, Ticket, User, UserRole, utc_now
from ..notifications import send_email

payments_bp = Blueprint("payments", __name__)


def fulfil_paid_order(order, payment_intent_id=None):
    """Mark an order paid and issue each ticket exactly once."""
    if order.status != OrderStatus.PAID:
        order.status = OrderStatus.PAID
    if payment_intent_id and not order.stripe_payment_intent_id:
        order.stripe_payment_intent_id = payment_intent_id
    missing = max(order.quantity - len(order.tickets), 0)
    for _ in range(missing):
        db.session.add(Ticket(event=order.event, order=order))
    db.session.commit()


def refund_paid_order(order):
    """Refund a destination charge and recover both transfer and app fee."""
    payment_intent = order.stripe_payment_intent_id
    if not payment_intent and order.stripe_checkout_session_id:
        session = stripe.checkout.Session.retrieve(order.stripe_checkout_session_id)
        payment_intent = session.payment_intent
    if not payment_intent:
        raise stripe.InvalidRequestError("The paid order has no Stripe payment reference.", None)
    refund = stripe.Refund.create(
        payment_intent=payment_intent,
        reverse_transfer=True,
        refund_application_fee=True,
        metadata={"eventspace_order_id": str(order.id), "reason": "event_cancelled"},
        idempotency_key=f"eventspace-event-cancel-order-{order.id}",
    )
    order.status = OrderStatus.REFUNDED
    return refund


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

    try:
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
    except stripe.InvalidRequestError as error:
        db.session.rollback()
        stripe_message = error.user_message or str(error)
        if "signed up for Connect" in stripe_message:
            return {
                "message": "Finish the one-time Stripe Connect platform setup, then try again.",
                "setupUrl": "https://dashboard.stripe.com/connect",
            }, 409
        current_app.logger.warning("Stripe rejected connected-account onboarding: %s", stripe_message)
        return {
            "message": f"Stripe could not start organiser onboarding: {stripe_message}",
        }, 400
    except stripe.StripeError:
        db.session.rollback()
        current_app.logger.exception("Stripe organiser onboarding failed")
        return {"message": "Stripe onboarding is temporarily unavailable. Please try again."}, 502
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

    ticket_subtotal_cents = event.ticket_price_cents * quantity
    booking_fee_cents = current_app.config["BOOKING_FEE_CENTS"]
    total_cents = ticket_subtotal_cents + booking_fee_cents
    fee_percent = current_app.config["STRIPE_PLATFORM_FEE_PERCENT"]
    platform_fee_cents = (ticket_subtotal_cents * fee_percent + 50) // 100 + booking_fee_cents
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
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": event.ticket_price_cents,
                        "product_data": {"name": event.title, "description": f"{event.venue}, {event.county}"},
                    },
                    "quantity": quantity,
                },
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": booking_fee_cents,
                        "product_data": {"name": "EventSpace booking fee", "description": "One flat fee per order"},
                    },
                    "quantity": 1,
                },
            ],
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
        .filter(Order.buyer_id == current_user.id, Order.status.in_((OrderStatus.PAID, OrderStatus.REFUNDED)))
        .order_by(Ticket.id.desc()).all()
    )
    return {"tickets": [{
        "id": ticket.id,
        "verificationCode": ticket.verification_code,
        "checkedInAt": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
        "orderStatus": ticket.order.status.value,
        "event": ticket.event.to_dict(),
    } for ticket in tickets]}


@payments_bp.post("/events/<int:event_id>/cancel")
@login_required
def cancel_event_and_refund(event_id):
    event = db.get_or_404(Event, event_id)
    if event.organiser_id != current_user.id and current_user.role != UserRole.ADMIN:
        return {"message": "You do not have permission to cancel this event."}, 403
    if event.status == EventStatus.CANCELLED and not event.orders.filter_by(status=OrderStatus.PAID).count():
        return {"message": "This event is already cancelled and all payments are refunded.", "refundedOrders": 0}
    if event.status not in (EventStatus.APPROVED, EventStatus.CANCELLED):
        return {"message": "Only a live event can use the cancellation and refund workflow."}, 409

    paid_orders = event.orders.filter_by(status=OrderStatus.PAID).all()
    if paid_orders and not configure_stripe():
        return {"message": "Stripe must be configured before paid tickets can be refunded."}, 503

    # Remove the listing immediately, preventing new checkout sessions while refunds run.
    event.status = EventStatus.CANCELLED
    db.session.commit()

    for order in event.orders.filter_by(status=OrderStatus.PENDING).all():
        if order.stripe_checkout_session_id:
            try:
                stripe.checkout.Session.expire(order.stripe_checkout_session_id)
            except stripe.StripeError:
                current_app.logger.warning("Could not expire checkout session for order %s", order.id)
        order.status = OrderStatus.FAILED
    db.session.commit()

    refunded = []
    failures = []
    for order in paid_orders:
        try:
            refund_paid_order(order)
            db.session.commit()
            refunded.append(order)
        except stripe.StripeError as error:
            db.session.rollback()
            failures.append({"orderId": order.id, "message": error.user_message or "Stripe rejected the refund."})

    for order in refunded:
        try:
            amount = f"€{order.total_cents / 100:.2f}"
            send_email(
                order.buyer.email,
                f"Event cancelled and refund issued: {event.title}",
                f"{event.title} has been cancelled. Your {amount} refund was issued to the original payment method. Your ticket is no longer valid. Banks can take several business days to display a refund.",
            )
        except Exception:
            current_app.logger.exception("Cancellation email failed for order %s", order.id)

    if failures:
        return {
            "message": f"The event is cancelled. {len(refunded)} order(s) were refunded, but {len(failures)} require another attempt.",
            "refundedOrders": len(refunded),
            "failedRefunds": failures,
        }, 502
    return {
        "message": f"Event cancelled and {len(refunded)} paid order(s) refunded.",
        "refundedOrders": len(refunded),
    }


@payments_bp.post("/checkout/confirm")
@login_required
def confirm_checkout():
    """Recover a paid checkout when a development webhook was unavailable."""
    if not configure_stripe():
        return {"message": "Stripe test mode is not configured yet."}, 503
    session_id = (request.get_json(silent=True) or {}).get("sessionId", "").strip()
    if not session_id:
        return {"message": "The checkout reference is missing."}, 400
    order = Order.query.filter_by(stripe_checkout_session_id=session_id, buyer_id=current_user.id).first()
    if not order:
        return {"message": "This checkout does not belong to your account."}, 404
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.StripeError:
        return {"message": "Stripe could not confirm this payment yet. Please try again."}, 502
    if session.payment_status != "paid":
        return {"message": "Stripe is still processing this payment."}, 409
    fulfil_paid_order(order, session.payment_intent)
    return {"confirmed": True, "ticketCount": len(order.tickets)}


@payments_bp.get("/check-in/events")
@login_required
def check_in_events():
    query = Event.query
    if current_user.role != UserRole.ADMIN:
        query = query.filter_by(organiser_id=current_user.id)
    events = query.order_by(Event.starts_at.desc()).all()
    return {"events": [{
        "id": event.id,
        "title": event.title,
        "startsAt": event.starts_at.isoformat(),
        "ticketsIssued": event.tickets.count(),
        "checkedIn": event.tickets.filter(Ticket.checked_in_at.isnot(None)).count(),
    } for event in events]}


@payments_bp.get("/check-in/events/<int:event_id>/tickets")
@login_required
def event_guest_list(event_id):
    event = db.get_or_404(Event, event_id)
    if current_user.role != UserRole.ADMIN and event.organiser_id != current_user.id:
        return {"message": "You cannot view another organiser's guest list."}, 403
    tickets = event.tickets.join(Order).order_by(User.last_name, User.first_name, Ticket.id).join(User, Order.buyer_id == User.id).all()
    return {"tickets": [{
        "id": ticket.id,
        "attendee": ticket.order.buyer.full_name,
        "email": ticket.order.buyer.email,
        "verificationCode": ticket.verification_code,
        "checkedInAt": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
    } for ticket in tickets]}


@payments_bp.post("/check-in")
@login_required
def check_in_ticket():
    data = request.get_json(silent=True) or {}
    code = data.get("verificationCode", "").strip()
    if code.startswith("eventspace://ticket/"):
        code = code.removeprefix("eventspace://ticket/")
    ticket = Ticket.query.filter_by(verification_code=code).first()
    if not ticket:
        return {"message": "This QR code is not a valid EventSpace ticket."}, 404
    if current_user.role != UserRole.ADMIN and ticket.event.organiser_id != current_user.id:
        return {"message": "This ticket belongs to another organiser's event."}, 403
    if ticket.order.status != OrderStatus.PAID or ticket.event.status == EventStatus.CANCELLED:
        return {"message": "This ticket was cancelled or refunded and is no longer valid."}, 409
    try:
        expected_event_id = int(data.get("eventId")) if data.get("eventId") else None
    except (TypeError, ValueError):
        return {"message": "Choose a valid event before checking in tickets."}, 400
    if expected_event_id and ticket.event_id != expected_event_id:
        return {"message": f"Valid ticket, but it is for {ticket.event.title}."}, 409
    if ticket.checked_in_at:
        return {
            "status": "already_checked_in",
            "message": "This ticket has already been checked in.",
            "checkedInAt": ticket.checked_in_at.isoformat(),
            "ticket": {
                "id": ticket.id,
                "attendee": ticket.order.buyer.full_name,
                "eventId": ticket.event_id,
                "eventTitle": ticket.event.title,
            },
        }
    ticket.checked_in_at = utc_now()
    db.session.commit()
    return {
        "status": "checked_in",
        "message": "Ticket accepted. Welcome in!",
        "checkedInAt": ticket.checked_in_at.isoformat(),
        "ticket": {
            "id": ticket.id,
            "attendee": ticket.order.buyer.full_name,
            "eventId": ticket.event_id,
            "eventTitle": ticket.event.title,
        },
    }


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
        if order and order.status in (OrderStatus.PENDING, OrderStatus.FAILED):
            fulfil_paid_order(order, stripe_object.get("payment_intent"))
            if order.event.status == EventStatus.CANCELLED:
                try:
                    refund_paid_order(order)
                    db.session.commit()
                except stripe.StripeError:
                    current_app.logger.exception("Urgent: refund failed for late completed order %s", order.id)
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
