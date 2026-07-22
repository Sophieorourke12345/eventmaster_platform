import secrets
from datetime import datetime, timedelta, timezone

import click

from .extensions import bcrypt, db
from .models import Event, EventStatus, User, UserRole


def register_commands(app):
    @app.cli.command("promote-admin")
    @click.argument("email")
    def promote_admin(email):
        """Promote an existing account to the administrator role."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            raise click.ClickException("No account exists with that email.")
        user.role = UserRole.ADMIN
        db.session.commit()
        click.echo(f"{user.email} is now an EventSpace administrator.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Add approved sample events for local design previews."""
        organiser = User.query.filter_by(email="demo-organiser@eventspace.local").first()
        if not organiser:
            organiser = User(
                first_name="EventSpace",
                last_name="Demo",
                email="demo-organiser@eventspace.local",
                password_hash=bcrypt.generate_password_hash(secrets.token_urlsafe(24)).decode("utf-8"),
                role=UserRole.ORGANISER,
                email_verified=True,
            )
            db.session.add(organiser)
            db.session.flush()

        samples = [
            ("Cork Harbour Sessions", "Music", "The Marina Market", "Cork", 2800, 220, 3),
            ("Dublin After Dark", "Nightlife", "The Button Factory", "Dublin", 1800, 300, 5),
            ("Galway Food Stories", "Food & Drink", "Spanish Arch", "Galway", 1200, 140, 8),
            ("Sunday Reset Workshop", "Education", "The Green Room", "Limerick", 3500, 60, 11),
            ("Comedy on the Coast", "Comedy", "Town Hall Theatre", "Clare", 2200, 180, 15),
            ("Summer City Run", "Sports", "Phoenix Park", "Dublin", 1500, 500, 20),
        ]
        added = 0
        for index, (title, category, venue, county, price, capacity, days) in enumerate(samples, 1):
            slug = f"demo-{index}-{title.lower().replace(' ', '-')}"
            if Event.query.filter_by(slug=slug).first():
                continue
            db.session.add(Event(
                title=title,
                slug=slug,
                description=f"A hand-picked {category.lower()} experience bringing people together in {county}. This sample listing demonstrates the EventSpace discovery and ticket journey.",
                venue=venue,
                county=county,
                starts_at=datetime.now(timezone.utc) + timedelta(days=days, hours=4),
                category=category,
                ticket_price_cents=price,
                ticket_capacity=capacity,
                status=EventStatus.APPROVED,
                organiser=organiser,
            ))
            added += 1
        db.session.commit()
        click.echo(f"Added {added} demo events.")

