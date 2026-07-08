# Folder Explanation

## Root Directory
| Path | Type | Purpose |
| :--- | :--- | :--- |
| `.github/workflows/` | CI/CD | GitHub Actions pipeline: lint → test → docker build |
| `backend/` | Backend | FastAPI REST API, ML model, training scripts, logs |
| `extension/` | Frontend | Chrome Manifest V3 extension for Gmail scanning |
| `migration/` | Docs | Flask-to-FastAPI migration report |
| `project-analysis/` | Docs | This documentation suite |
| `docker-compose.yml` | Config | Orchestrates API + Redis containers |
| `railway.json` | Config | Railway.app cloud deployment settings |
| `README.md` | Docs | User-facing project documentation |

---

## `/backend` — Python ML Backend
The core server runtime. Houses the FastAPI application, all ML pipelines, feature engineering, external integrations, and infrastructure configs.

| File/Folder | Why It Exists |
| :--- | :--- |
| `app.py` | **Entry point.** FastAPI app definition, Pydantic request models, route handlers, error handlers, rate limiter, model loading, SQLite logging. |
| `features.py` | Extracts 17 numeric features from a raw URL. Called by `predict_url()` in `app.py` and by training/evaluation scripts. |
| `reputation.py` | Aggregates PhishTank, VirusTotal, and WHOIS lookups into a single reputation score. Called by `/reputation` endpoint. |
| `cache.py` | Redis get/set/stats with graceful fallback. Called by `/predict` endpoint. |
| `logger.py` | Configures dual-output logging (file + console). Imported by `app.py` and `reputation.py`. |
| `train_model.py` | Offline script: loads CSV, extracts features, runs RandomizedSearchCV, saves model PKL, logs to MLflow. |
| `evaluate.py` | Offline script: loads saved model, generates confusion matrix, ROC curve, feature importance plots. |
| `compare_models.py` | Offline script: trains RF, GB, LR side-by-side and saves comparison CSV. |
| `benchmark.py` | Offline script: measures `/predict` latency for 10 test URLs against running server. |
| `test_api.py` | Integration test suite (23 assertions) against a running server instance. |
| `mlflow_tracking.py` | Helper to set up MLflow experiment and log params/metrics/model artifacts. |
| `gunicorn.conf.py` | Production Gunicorn config with `UvicornWorker` for ASGI support. |
| `requirements.txt` | Pinned Python dependencies. |
| `Dockerfile` | Multi-stage Docker build (builder + production). |
| `model_card.md` | Model documentation: dataset, features, performance, limitations. |
| `model/` | Serialized model binaries: `phishing_model.pkl`, `feature_names.pkl`. |
| `logs/` | SQLite database `requests.db` and daily log files `app_YYYYMMDD.log`. |
| `mlflow/` | MLflow SQLite tracking database. |
| `mlruns/` | MLflow run metadata and artifacts. |

**Relationship:** `app.py` imports from `features.py`, `reputation.py`, `cache.py`, `logger.py`. Training scripts import `features.py` and `mlflow_tracking.py`.

---

## `/extension` — Chrome Browser Extension
The client-side component running inside Google Chrome on Gmail pages.

| File | Why It Exists |
| :--- | :--- |
| `manifest.json` | Chrome Manifest V3 config: permissions, content scripts, popup, icons. |
| `content.js` | Injected into Gmail. Monitors DOM, extracts links, runs NLP scoring, sends to backend, injects badges, blocks dangerous clicks. |
| `background.js` | Service worker. Initializes stats counters on extension install. |
| `popup.html` | Extension popup dashboard showing scan statistics and backend status. |
| `popup.js` | Reads `chrome.storage.local` stats and checks `/health` endpoint. |
| `styles.css` | Styles for injected badges, tooltips, and click-blocked links. |
| `icons/` | 16x16, 48x48, 128x128 extension icons. |

**Relationship:** `content.js` communicates with the backend via HTTP to `127.0.0.1:5000/predict`. `popup.js` pings `127.0.0.1:5000/health`.

---

## `/.github/workflows`
Contains `ci.yml` — the GitHub Actions pipeline triggered on push/PR to `main`. Three jobs: `lint` (flake8), `test` (boots FastAPI + Redis, runs 23 tests), `docker` (builds and validates Docker image).
