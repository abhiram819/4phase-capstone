# NetPulse API

NetPulse is a FastAPI network-monitoring API with device routes, service rules, offline alerts, and interchangeable in-memory, MongoDB, and MySQL repositories. The MongoDB repository uses separate `devices` and `alerts` collections.

## Setup

Create and activate a virtual environment, install dependencies, and configure MongoDB:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `MONGODB_URI`, `MONGODB_DB_NAME`, `DEVICES_COLLECTION`, and `ALERTS_COLLECTION` in `.env`. The example selects `DATABASE_BACKEND=mongodb`; MongoDB must be reachable before starting the API. Set `DATABASE_BACKEND=memory` for isolated in-memory runs, or `DATABASE_BACKEND=mysql` to use the existing MySQL backend and its Alembic migrations.

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; Swagger UI is at `/docs` and the generated API contract is at `/openapi.json`. The six endpoints are `POST /devices`, `GET /devices`, `GET /devices/{device_id}`, `PATCH /devices/{device_id}/status`, `GET /alerts`, and `GET /health`. The request models provide Swagger examples; routes document their 404 and 409 responses. FastAPI builds `/openapi.json` from these route and Pydantic model declarations.

## MongoDB Collections And Indexes

On application startup, MongoDB mode creates the configured collections and ensures a unique `devices.device_id` index plus `alerts.device_id` and `alerts.timestamp` indexes. Index creation is idempotent. Verify the setup from the project root:

```bash
python -c "from app.db.mongo import get_db; from app.db.collections import ensure_indexes; db = get_db(); ensure_indexes(db); print(db.list_collection_names(), db.devices.index_information())"
```

The `devices` documents retain the API device fields, including optional `location`; older documents without `location` load as `null`. MongoDB's internal `_id` is removed during deserialization. Alerts store the device ID, message, and UTC timestamp.

## Tests And Architecture

Run the service and repository tests with:

```bash
python -m pytest -q
```

The service depends on a repository protocol. The repository owns persistence, routes map service errors to HTTP responses, and `app/events.py` records an alert only after an existing device transitions from online to offline. The service tests use a fresh in-memory repository; MongoDB repository and index tests use isolated fakes and do not require a live server. MySQL remains available with its existing Alembic migrations.