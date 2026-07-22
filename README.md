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

Ticket prices are stored in cents. For each successful order, EventSpace receives a 4% organiser commission plus one transparent €1 customer booking fee. The booking fee is charged once per order, not per ticket. Stripe processing fees are deducted from the platform balance, and EventSpace retains the remainder. Full event-cancellation refunds return the ticket subtotal and booking fee and reverse the organiser transfer and application fee.

## Stripe test mode

1. Activate Connect in a Stripe test-mode account.
2. Add `STRIPE_SECRET_KEY` to the root `.env` file.
3. Forward Stripe events to `/api/payments/webhook` and add the signing secret as `STRIPE_WEBHOOK_SECRET`.
4. Keep `STRIPE_PLATFORM_FEE_PERCENT=4`.
5. Sign in as an organiser and use **Connect with Stripe** in the organiser hub.

The checkout uses a Stripe Connect destination charge. EventSpace collects the 4% application fee and transfers the remainder to the verified organiser. Checkout Sessions reserve inventory for 30 minutes. Tickets are issued only after a signed `checkout.session.completed` webhook confirms payment.

For local webhook testing with Stripe CLI:

```bash
stripe listen --forward-to localhost:5000/api/payments/webhook
```

Never add Stripe keys to the source code or commit `.env`.

## Tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v

cd ../frontend
npm run build
```

## Production deployment

The repository includes a Docker-based Render Blueprint. It builds the Vue app, serves it from Flask/Gunicorn, runs database migrations at startup, and stores SQLite data plus event uploads on an encrypted persistent disk.

1. In Render, create a Blueprint from this GitHub repository.
2. Add the Stripe and mail secrets requested by `render.yaml`.
3. After deployment, set `FRONTEND_URL` and `PUBLIC_URL` to the final HTTPS domain.
4. Register `/api/payments/webhook` in Stripe and subscribe to `checkout.session.completed`, `checkout.session.expired`, and `account.updated`.
5. Add the final domain to Google Search Console and submit `/sitemap.xml`.
