# המחלץ — Backend

FastAPI backend for the Hamachletz (המחלץ) emergency management platform.

**Run the full stack (backend + frontend + PostgreSQL) in one command:** from the project root run `docker compose up --build`. See the root [README](../README.md).

---

## How to run the backend (local)

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

Edit `.env` and set at least **DATABASE_URL**, **SECRET_KEY**, and **ADMIN_PASSWORD** (see [Database](#database) and [Environment variables](#environment-variables)).

### 3. Database migrations

```bash
alembic upgrade head
```

### 4. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

---

## Admin access

There is a single admin account. Set **ADMIN_PASSWORD** in `.env` (e.g. `ADMIN_PASSWORD=your-secure-password`). Log in at `/login` with that password. No user table or email is used.

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

## WhatsApp (optional)

Volunteer access is **link-based**: the admin shares an event join URL; no email is sent. Optional **WhatsApp** (see env table) can send the event link when configured; leave **WHATSAPP_PROVIDER** unset to use link sharing only.


## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| **DATABASE_URL** | PostgreSQL connection URL | (required) |
| **SECRET_KEY** | JWT signing key (e.g. `openssl rand -hex 32`) | (required in production) |
| **ADMIN_PASSWORD** | Single admin password (log in at /login) | (required) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Admin JWT expiry (minutes) | 1440 |
| CORS_ORIGINS | Allowed origins (comma-separated) | http://localhost:5173, http://127.0.0.1:5173 |
| DEBUG | If true, extra logging | false |
| **WhatsApp** (optional; volunteer invites are link-based by default) | | |
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
- **401 on /admin or /login** — Set **ADMIN_PASSWORD** in `.env` and use that password at `/login`.
- **Twilio 63007** (“could not find a Channel with the specified From address”) — **TWILIO_WHATSAPP_FROM** must be your Twilio WhatsApp sender. In Twilio: **Messaging → Try it out → Send a WhatsApp message**, copy the sandbox number (e.g. `+14155238886`), set `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886`, and join the sandbox from your phone.
- **Twilio 63031** (same To and From) — You cannot send to the same number as your Twilio sender. The app skips that volunteer and logs “WhatsApp skip: same To and From”. Use a different volunteer phone for testing.
