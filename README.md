# NetPulse API

NetPulse is a FastAPI network-monitoring API with device routes, service rules, repository-backed storage, offline alerts, and Alembic-managed MySQL schema migrations.

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The API defaults to in-memory storage, which is useful for local exploration and resets on restart. To use MySQL, create the `netpulse_db` database, copy `.env.example` to `.env`, and set the MySQL host, port, database, user, password, and `DATABASE_URL` for your environment. Apply the schema:

```bash
alembic upgrade head
alembic current
```

Start the API with `DATABASE_BACKEND=mysql` in `.env`:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`. Set `DATABASE_BACKEND=memory` to use the in-memory repository.

## Migrations And Tests

The initial migration creates `devices` and `alerts`. The next migration adds the optional `location` field to devices. To inspect the migration history or undo the latest schema change:

```bash
alembic history
alembic downgrade -1
alembic upgrade head
```

Run the unit and isolated SQLAlchemy repository tests with:

```bash
python -m pytest -q
```

The service depends on a repository protocol, so business rules and offline-alert behavior are shared by the in-memory and MySQL implementations. FastAPI generates `/openapi.json` from the route declarations and Pydantic schemas; Swagger UI renders it at `/docs`.