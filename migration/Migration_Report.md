# Flask to FastAPI Migration Report

This report documents the migration of the PhishGuard AI backend REST API from Flask to FastAPI, ensuring complete behavioral parity and production readiness.

---

## 1. Summary of Changes

| Metric | Details |
| :--- | :--- |
| **Old Framework** | Flask (WSGI) |
| **New Framework** | FastAPI (ASGI) |
| **Server Engine** | Uvicorn (booted via UvicornWorker inside Gunicorn) |
| **Status** | Production-ready, 100% backward-compatible |

---

## 2. File Level Changes

### [backend/app.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/app.py)
*   **Action:** [MODIFY]
*   **Description:** Replaced Flask server instance and decorators with `FastAPI` instance and route methods (`@app.get`, `@app.post`). Incorporated `Pydantic` models for JSON payload validation. Replaced `flask-limiter` with `slowapi` rate limiting.
*   **Parity Safeguards:** Custom exception handlers intercept `StarletteHTTPException` to transform default FastAPI 404/405 error responses into Flask-matching responses (e.g. `{"error": "Endpoint not found"}`). Handled unhandled exceptions with a generic handler.

### [backend/requirements.txt](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/requirements.txt)
*   **Action:** [MODIFY]
*   **Description:** Removed Flask-related libraries (`flask`, `flask-cors`, `flask-limiter`). Added `fastapi`, `uvicorn`, and `slowapi`.

### [backend/gunicorn.conf.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/gunicorn.conf.py)
*   **Action:** [MODIFY]
*   **Description:** Changed the Gunicorn worker class from `"sync"` to `"uvicorn.workers.UvicornWorker"`. Removed the WSGI-specific `preload_app = True` setting to prevent async/event-loop sharing issues on worker forks.

### [.github/workflows/ci.yml](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/.github/workflows/ci.yml)
*   **Action:** [MODIFY]
*   **Description:** Updated the start-up service check step to reference "FastAPI" instead of "Flask". The execution command `python app.py &` continues to function natively.

---

## 3. Dependency Summary

### Removed Packages
*   `flask==3.1.3`
*   `flask-cors==6.0.2`
*   `flask-limiter==4.1.1`

### Added Packages
*   `fastapi==0.111.0` (Core framework)
*   `uvicorn==0.30.1` (ASGI runner engine)
*   `slowapi==0.1.9` (Rate limiting engine compatible with FastAPI/limits)

---

## 4. Migrated Endpoints and Logic

| Method | Endpoint | Description | Input Model (Pydantic) | Output Format | Rate Limited? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | Service health status. | None | JSON dict | No |
| **POST** | `/predict` | Predicts maliciousness of a URL. | `PredictRequest` | JSON dict | Yes (30/min per IP) |
| **POST** | `/analyze` | Batch URL and sender checks. | `AnalyzeRequest` | JSON dict | No |
| **GET** | `/logs` | Fetches recent scan logs from SQLite. | None | JSON list of dicts | No |
| **POST** | `/reputation` | Resolves VT/PhishTank threat scores. | `ReputationRequest` | JSON dict | No |
| **GET** | `/cache` | Returns Redis cache usage stats. | None | JSON dict | No |

---

## 5. Compatibility and Integration Audits

*   **API Response Consistency:** All response structures are preserved down to the exact keys. Manual validation checks inside endpoints return the original Flask response payload `{"error": "..."}` with `400` status codes rather than raising Pydantic validation errors (which return 422).
*   **Chrome Extension Compatibility:** Because the backend port matches (`5000`) and the API path structures remain unchanged, the Chrome extension operates seamlessly without any modifications to `content.js` or `popup.js`.
*   **Database (SQLite) Integration:** The SQLite logging database uses parameterized writing, which was preserved during migration.
*   **Cache (Redis) Integration:** The Redis connector and MD5 hashing logic functions identically.

---

## 6. Execution Instructions

### Running Locally (Development Mode)
Run the application using Python:
```bash
python backend/app.py
```
Or run Uvicorn directly from the `/backend` directory:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Running with Docker / Gunicorn (Production Mode)
Launch the Gunicorn runner:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 -k uvicorn.workers.UvicornWorker app:app
```
Or use Docker Compose to spin up the entire stack:
```bash
docker-compose up --build
```
