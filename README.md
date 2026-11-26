# NetPulse API

A small FastAPI modular monolith with device routes, service logic, an in-memory repository, and offline alerts.

Install dependencies and start the development server:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`. Device and alert data are held in memory and reset when the process restarts.

To verify offline alerts in Swagger, register an online device, PATCH its status to `offline` twice, then call `GET /alerts`. Only the first transition creates an alert.

FastAPI generates `/openapi.json` from route declarations and Pydantic request/response models. Swagger UI renders that schema at `/docs`.