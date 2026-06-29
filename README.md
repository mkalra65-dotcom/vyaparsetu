# VyaparSetu

Clean-room backend foundation for VyaparSetu.

## Backend Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- JWT authentication
- Docker Compose

## Local Setup

Create an environment file:

```bash
cp .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d db
```

Create and activate a Python virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Optional: create the first admin user by setting these values in `.env`:

```bash
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=change-this-password
```

Then run:

```bash
python -m app.cli create-first-admin
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- Health check: http://localhost:8000/health
- OpenAPI docs: http://localhost:8000/docs

Uploaded development files are stored under `backend/storage/uploads/{application_id}/`.

Run Phase 3 workflow verification:

```bash
cd backend
python scripts/verify_phase3.py
```

## Docker Compose Backend

To run PostgreSQL and the backend together:

```bash
cp .env.example .env
docker compose up --build
```

Run migrations in the backend container:

```bash
docker compose exec backend alembic upgrade head
```

Create the first admin in Docker after setting `FIRST_ADMIN_EMAIL` and
`FIRST_ADMIN_PASSWORD` in `.env`:

```bash
docker compose exec backend python -m app.cli create-first-admin
```
