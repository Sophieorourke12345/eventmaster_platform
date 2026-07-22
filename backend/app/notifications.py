import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(recipient, subject, text):
    """Send configured transactional mail; remain a no-op in local development."""
    username = current_app.config["MAIL_USERNAME"]
    password = current_app.config["MAIL_PASSWORD"]
    if not recipient or not username or not password:
        return False
    message = EmailMessage()
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    with smtplib.SMTP_SSL(current_app.config["MAIL_HOST"], current_app.config["MAIL_PORT"], timeout=10) as server:
        server.login(username, password)
        server.send_message(message)
    return True


def notify_event_submission(event):
    admin_url = f"{current_app.config['FRONTEND_URL'].rstrip('/')}/admin"
    send_email(
        current_app.config["ADMIN_EMAIL"],
        f"EventSpace review: {event.title}",
        "\n".join([
            "A new event is ready for verification.", "",
            f"Event: {event.title}",
            f"Organiser: {event.organiser.full_name} ({event.organiser.email})",
            f"Location: {event.venue}, {event.county}",
            f"Images submitted: {len(event.images)}", "",
            f"Sign in to review every detail and image: {admin_url}",
        ]),
    )
    send_email(
        event.organiser.email,
        f"We received {event.title}",
        f"Your event is now pending EventSpace verification. We will notify you after it has been reviewed.",
    )

