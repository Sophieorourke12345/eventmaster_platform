# EventSpace

A clean full-stack rebuild of the original EventMaster prototype. EventSpace lets attendees discover verified events and lets organisers submit events, sell tickets, and receive payouts after platform review.

## Architecture

- `frontend/`: Vue 3, Vue Router, Pinia, and Vite
- `backend/`: Flask application factory, SQLAlchemy models, Flask-Login sessions, and REST API blueprints
- Stripe Connect will provide organiser onboarding, checkout, payouts, and a 4% EventSpace application fee

## Local setup

Copy `.env.example` to `.env` and replace the development values. Never commit `.env`.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run.py db upgrade
flask --app run.py run --debug
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` and `/uploads` to Flask on port 5000.

## Event lifecycle

1. A signed-in user submits an event and becomes an organiser.
2. The event is stored as `pending` and is not public.
3. An administrator reviews the complete listing and approves or rejects it with a reason.
4. Approved events appear in public discovery and can sell tickets.
5. Stripe verifies and onboards the organiser separately for payouts.

## Payment rule

Ticket prices are stored in cents. For each successful sale, EventSpace records a 4% platform fee. Stripe processing fees are separate and the final fee-bearing arrangement must be confirmed before production launch.

