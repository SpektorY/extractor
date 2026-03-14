# המחלץ (Hamachletz)

פלטפורמה לניהול אירועי חירום: חמ״ל (מערכת ניהול), מתנדבים בשטח (Mobile Web), והזנקה בווטסאפ.

## Stack

- **Backend:** Python 3.9+, FastAPI, PostgreSQL, SQLAlchemy 2, Alembic
- **Frontend:** TypeScript, React (Vite), shadcn/ui, React Router, TanStack Query

---

## How to run the system

You need **Python 3.9+**, **Node.js 18+**, and **PostgreSQL** installed.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL and SECRET_KEY (see backend/README.md)
alembic upgrade head
python -m scripts.create_admin   # Create first admin user (email + password when prompted)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

### 2. Frontend

```bash
cd frontend
npm install
# Optional: create .env with VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

- App: http://localhost:5173  
- Admin login: http://localhost:5173/login  

---

## Backend setup (details)

All backend configuration is documented in **[backend/README.md](backend/README.md)**:

| Topic | Section in backend/README.md |
|-------|-----------------------------|
| **How to create an admin user** | [Create admin user](backend/README.md#create-admin-user) |
| **How to connect to the database** | [Database](backend/README.md#database) |
| **How to add email for password reset** | [Password reset email](backend/README.md#password-reset-email) |
| **How to connect to WhatsApp** (volunteer invites) | [WhatsApp](backend/README.md#whatsapp) |

---

## Project structure

- `backend/app` — FastAPI: core, models, schemas, api/v1/endpoints, services
- `backend/alembic` — DB migrations
- `backend/scripts` — e.g. `create_admin` for first admin user
- `frontend/src` — React: features (admin, volunteer, public), components, lib

## Tests

```bash
cd backend
pip install pytest httpx python-multipart
pytest tests/ -v
```
