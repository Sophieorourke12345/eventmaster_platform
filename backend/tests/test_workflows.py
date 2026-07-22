import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app
from app.extensions import bcrypt, db
from app.models import Event, EventStatus, Order, OrderStatus, Ticket, User, UserRole


class EventSpaceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-only",
            "STRIPE_SECRET_KEY": "sk_test_fake",
            "STRIPE_WEBHOOK_SECRET": "whsec_fake",
        })
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        self.csrf = self.client.get("/api/auth/csrf").get_json()["csrfToken"]

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def request(self, method, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["X-CSRFToken"] = self.csrf
        return self.client.open(path, method=method, headers=headers, **kwargs)

    def register(self, email="buyer@example.com"):
        return self.request("POST", "/api/auth/register", json={
            "firstName": "Ticket", "lastName": "Buyer",
            "email": email, "password": "password123",
        })

    def test_event_stays_private_until_admin_approval(self):
        self.assertEqual(self.register("admin@example.com").status_code, 201)
        created = self.request("POST", "/api/events", json={
            "title": "Cork Music Night", "description": "A complete event description",
            "venue": "City Hall", "county": "Cork",
            "startsAt": "2026-09-12T19:30:00+00:00", "category": "Music",
            "ticketPriceCents": 2500, "ticketCapacity": 80,
        })
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/api/events").get_json()["events"], [])
        event_id = created.get_json()["event"]["id"]
        with self.app.app_context():
            user = User.query.filter_by(email="admin@example.com").first()
            user.role = UserRole.ADMIN
            db.session.commit()
        self.assertEqual(self.client.get("/api/events/admin/overview").status_code, 200)
        decision = self.request("POST", f"/api/events/{event_id}/decision", json={"decision": "approved"})
        self.assertEqual(decision.status_code, 200)
        results = self.client.get("/api/events?category=Music&county=Cork&minPrice=20&maxPrice=30").get_json()["events"]
        self.assertEqual(len(results), 1)

    def test_stripe_webhook_issues_tickets_and_records_four_percent_fee(self):
        with self.app.app_context():
            organiser = User(
                first_name="Event", last_name="Host", email="host@example.com",
                password_hash=bcrypt.generate_password_hash("password123").decode(),
                role=UserRole.ORGANISER, stripe_account_id="acct_test",
                stripe_charges_enabled=True, stripe_payouts_enabled=True,
            )
            db.session.add(organiser)
            db.session.flush()
            event = Event(
                title="Paid Test", slug="paid-test", description="Payment test",
                venue="Venue", county="Cork",
                starts_at=datetime.now(timezone.utc) + timedelta(days=4), category="Music",
                ticket_price_cents=2500, ticket_capacity=20,
                status=EventStatus.APPROVED, organiser=organiser,
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        self.assertEqual(self.register().status_code, 201)
        account = SimpleNamespace(charges_enabled=True, payouts_enabled=True)
        session = SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test/session")
        with patch("app.api.payments.stripe.Account.retrieve", return_value=account), patch("app.api.payments.stripe.checkout.Session.create", return_value=session):
            checkout = self.request("POST", "/api/payments/checkout", json={"eventId": event_id, "quantity": 2})
        self.assertEqual(checkout.status_code, 200)

        with self.app.app_context():
            order = Order.query.one()
            self.assertEqual(order.platform_fee_cents, 200)
            self.assertEqual(order.status, OrderStatus.PENDING)

        stripe_event = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_123", "payment_status": "paid", "payment_intent": "pi_test"}}}
        with patch("app.api.payments.stripe.Webhook.construct_event", return_value=stripe_event):
            webhook = self.client.post("/api/payments/webhook", data=b"{}", headers={"Stripe-Signature": "test"})
        self.assertEqual(webhook.status_code, 200)
        with self.app.app_context():
            self.assertEqual(Order.query.one().status, OrderStatus.PAID)
            self.assertEqual(Ticket.query.count(), 2)


if __name__ == "__main__":
    unittest.main()

