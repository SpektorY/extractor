# Backend (FastAPI + PostgreSQL client)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App and migrations
COPY . .

# Run migrations then the API (override CMD when using for one-off migrations)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
