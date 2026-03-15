# המחלץ (Hamachletz)

פלטפורמה לניהול אירועי חירום: חמ״ל (מערכת ניהול), מתנדבים בשטח (Mobile Web), והזנקה בווטסאפ.

## Stack

- **Backend:** Python 3.9+, FastAPI, PostgreSQL, SQLAlchemy 2, Alembic
- **Frontend:** TypeScript, React (Vite), shadcn/ui, React Router, TanStack Query

---

## How to run the system

### Option A: Docker Compose (recommended for developers)

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (or Docker Desktop, which includes Compose).

**First time (or after pulling):**

```bash
# From the project root (where docker-compose.yml is)
docker compose up --build
```

Wait until you see the backend log line like `Uvicorn running on http://0.0.0.0:8000` and the frontend line like `Local: http://localhost:5173/`. Then:

| What | URL |
|------|-----|
| **App** | http://localhost:5173 |
| **Admin login** | http://localhost:5173/login (password: `admin` unless you set `ADMIN_PASSWORD`) |
| **API docs** | http://localhost:8000/docs |

**Optional:** To set a custom admin password or secret key, copy the example env and edit:

```bash
cp .env.example .env
# Edit .env: set ADMIN_PASSWORD and SECRET_KEY
```

Then run `docker compose up --build` again (or restart the backend container). No `.env` is required for a quick local run; defaults work.

**Useful commands:**

- Stop: `Ctrl+C` then `docker compose down`
- Run in background: `docker compose up -d --build`
- View logs: `docker compose logs -f`

### Option B: Local (Python + Node + PostgreSQL)

You need **Python 3.9+**, **Node.js 18+**, and **PostgreSQL** installed.

#### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL, SECRET_KEY, and ADMIN_PASSWORD (see backend/README.md)
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

#### 2. Frontend

```bash
cd frontend
npm install
# Optional: create .env with VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

- App: http://localhost:5173  
- Admin login: http://localhost:5173/login  

---

## Configuration

Backend configuration is in **[backend/README.md](backend/README.md)**; frontend (optional env) is in **[frontend/README.md](frontend/README.md)**.

| Topic | Section in backend/README.md |
|-------|-----------------------------|
| **Admin access** (single password) | [Admin access](backend/README.md#admin-access) |
| **How to connect to the database** | [Database](backend/README.md#database) |
| **How to connect to WhatsApp** (optional; volunteer invites are link-based) | [WhatsApp](backend/README.md#whatsapp-optional) |

---

## Project structure

- `backend/app` — FastAPI: core, models, schemas, api/v1/endpoints, services
- `backend/alembic` — DB migrations
- `backend/scripts` — utility scripts (if any)
- `frontend/src` — React: features (admin, volunteer, public), components, lib

## Tests

```bash
cd backend
pip install pytest httpx python-multipart
pytest tests/ -v
```
