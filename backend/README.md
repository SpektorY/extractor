# המחלץ — Backend

FastAPI backend for the Hamachletz (המחלץ) emergency management platform.

---

## How to run the backend

### 1. Virtualenv and dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
```

Edit `.env` and set at least **DATABASE_URL** and **SECRET_KEY** (see [Database](#database) and the [Environment variables](#environment-variables) table below).

### 3. Database migrations

```bash
alembic upgrade head
```

### 4. Create first admin user

```bash
python -m scripts.create_admin
```

Enter email and password when prompted. Then start the server.

### 5. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

---

## Create admin user

**Command:** from the `backend` directory (with venv active):

```bash
python -m scripts.create_admin
```

You will be prompted for:

- **Admin email** — used to log in at `/login`
- **Password** — at least 6 characters (input is hidden)

The script creates a single user in the `users` table with `is_active=True`. There is no admin signup UI; this script is the intended way to create the first admin (and any additional admins).

**Is this the right way?** Yes. Admin users are not created through the app. Use this script whenever you need a new admin account (e.g. first deploy or new team member). If you run it with an email that already exists, the script reports "User already exists" and exits.

---

## Database

### Connect with PostgreSQL

Set **DATABASE_URL** in `.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Examples:

- Local: `postgresql://postgres:postgres@localhost:5432/hamachletz`
- With SSL: `postgresql://user:pass@host:5432/db?sslmode=require`

### Create the database (if it doesn’t exist)

PostgreSQL does not create the database for you. Create it once, then run migrations:

```bash
# Using psql or your DB tool:
createdb hamachletz

# Or in psql:
# CREATE DATABASE hamachletz;
```

Then run:

```bash
alembic upgrade head
```

### Troubleshooting

- **"relation does not exist"** — Run `alembic upgrade head`.
- **"could not connect to server"** — Check that PostgreSQL is running and that **DATABASE_URL** (host, port, user, password, database name) is correct.

---

## Password reset email

To send real password reset emails (instead of the stub), set the following in `.env`.

### Option A — SMTP (Gmail, Outlook, or any SMTP server)

```env
EMAIL_BACKEND=smtp
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=המחלץ
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
```

### Option B — Resend (https://resend.com, free tier available)

```env
EMAIL_BACKEND=resend
EMAIL_FROM=onboarding@yourdomain.com   # must be a verified domain in Resend
RESEND_API_KEY=re_xxxx
```

### Without configuration

If **EMAIL_BACKEND** is unset, no email is sent. With **DEBUG=true**, the reset link is printed to the backend console and can be returned in the API response for local testing.

---

## WhatsApp

Volunteer invites are sent from the control room (**"שלח שוב הזמנות לכולם"** or when attaching volunteers). Each volunteer gets a WhatsApp message with the event name, address, and a magic link. No message is sent until a provider is configured.

### Without configuration

If **WHATSAPP_PROVIDER** is unset, the API still returns success (so the UI works), but no WhatsApp is sent. With **DEBUG=true**, the backend logs the link to the console for testing.

### Connect with Twilio

1. **Sign up:** [Twilio](https://www.twilio.com/) and create an account.
2. **WhatsApp Sandbox** (easiest for testing):
   - In Twilio Console: **Messaging → Try it out → Send a WhatsApp message**.
   - Join the sandbox by sending the shown code from your phone to the Twilio number.
3. **Credentials:** Twilio Console → **Account** → Account Info: **Account SID** and **Auth Token**.
4. **WhatsApp “From” number:** For the sandbox it looks like `whatsapp:+14155238886` (the number shown in the sandbox step). For production use a Twilio WhatsApp-enabled number.
5. **Set in `.env`:**

```env
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

6. **Magic links:** Volunteers receive a link like `https://your-domain.com/event/TOKEN`. Set **FRONTEND_BASE_URL** in `.env` to your real frontend URL (e.g. `https://app.yourdomain.com`). For local testing you can use a tunnel (e.g. ngrok) and set `FRONTEND_BASE_URL=https://your-ngrok-url.ngrok.io`.

**Phone format:** The backend normalizes Israeli numbers: if the volunteer’s phone doesn’t start with `+`, it’s prefixed with `+972` (e.g. `0501234567` → `+972501234567`).

**Important:** **TWILIO_WHATSAPP_FROM** must be Twilio’s WhatsApp sender (sandbox or your Twilio WhatsApp number), not a volunteer’s number. If a volunteer’s phone is the same as the From number, that invite is skipped (Twilio error 63031).

### GreenAPI

The code has a placeholder for **GreenAPI** (`WHATSAPP_PROVIDER=greenapi`). It is not fully implemented; only Twilio is supported for real sends.

---

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| **DATABASE_URL** | PostgreSQL connection URL | (required) |
| **SECRET_KEY** | JWT signing key (e.g. `openssl rand -hex 32`) | (required in production) |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT expiry (minutes) | 1440 |
| MAGIC_LINK_EXPIRE_MINUTES | Volunteer magic link expiry (minutes) | 1440 |
| CORS_ORIGINS | Allowed origins (comma-separated) | http://localhost:5173, http://127.0.0.1:5173 |
| FRONTEND_BASE_URL | Base URL for magic links in WhatsApp | http://localhost:5173 |
| DEBUG | If true, reset link and WhatsApp link can be printed to console | false |
| **Email (password reset)** | | |
| EMAIL_BACKEND | `smtp` or `resend` — leave unset for no email | (optional) |
| EMAIL_FROM | Sender address | (optional) |
| EMAIL_FROM_NAME | Sender display name | המחלץ |
| SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS | When EMAIL_BACKEND=smtp | (optional) |
| RESEND_API_KEY | When EMAIL_BACKEND=resend (get key at resend.com) | (optional) |
| **WhatsApp** | | |
| WHATSAPP_PROVIDER | `twilio` or `greenapi` | (optional) |
| TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM | When WHATSAPP_PROVIDER=twilio | (optional) |

---

## Tests

```bash
pip install pytest httpx python-multipart
pytest tests/ -v
```

---

## Troubleshooting

- **"relation does not exist"** — Run `alembic upgrade head`.
- **"could not connect to server"** — PostgreSQL running? **DATABASE_URL** correct (host, port, user, password, db name)?
- **401 on /admin or /login** — Create an admin with `python -m scripts.create_admin` and log in at `/login`.
- **Twilio 63007** (“could not find a Channel with the specified From address”) — **TWILIO_WHATSAPP_FROM** must be your Twilio WhatsApp sender. In Twilio: **Messaging → Try it out → Send a WhatsApp message**, copy the sandbox number (e.g. `+14155238886`), set `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886`, and join the sandbox from your phone.
- **Twilio 63031** (same To and From) — You cannot send to the same number as your Twilio sender. The app skips that volunteer and logs “WhatsApp skip: same To and From”. Use a different volunteer phone for testing.
