# File Documentation

---

## Backend Core Files

### [app.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/app.py)
**Purpose:** Main FastAPI application — the entry point for the REST API server.

**Imports:**
- `fastapi`: `FastAPI`, `Request`, `status`
- `fastapi.responses`: `JSONResponse`
- `fastapi.middleware.cors`: `CORSMiddleware`
- `starlette.exceptions`: `HTTPException as StarletteHTTPException`
- `pydantic`: `BaseModel`, `Field`
- `typing`: `List`, `Optional`
- `slowapi`: `Limiter`, `_rate_limit_exceeded_handler`
- `slowapi.util`: `get_remote_address`
- `slowapi.errors`: `RateLimitExceeded`
- Local: `reputation.get_reputation`, `logger.logger`, `cache.get_cached/set_cached/get_cache_stats`, `features.extract_features`
- Stdlib: `joblib`, `os`, `sys`, `time`, `sqlite3`, `datetime`

**Pydantic Request Models:**
- `PredictRequest(url: Optional[str])` — used by `/predict`
- `AnalyzeRequest(email_text, urls: List[str], sender)` — used by `/analyze`
- `ReputationRequest(url: Optional[str])` — used by `/reputation`

**Key Functions:**
| Function | Purpose | Called By |
| :--- | :--- | :--- |
| `init_db()` | Creates SQLite `logs` table if absent | Module-level at import time |
| `log_request(url, pred, prob, ms)` | Inserts prediction record into SQLite | `predict()`, `analyze()` |
| `predict_url(url)` | Sanitizes URL, extracts features, runs model inference | `predict()`, `analyze()` |
| `get_threat_level(prob)` | Maps probability to tier string | `predict()`, `analyze()` |

**Route Handlers:**
| Decorator | Function | Rate Limited |
| :--- | :--- | :--- |
| `@app.get('/health')` | `health()` | No |
| `@app.post('/predict')` | `predict(request, payload)` | Yes (30/min) |
| `@app.post('/analyze')` | `analyze(request, payload)` | No |
| `@app.get('/logs')` | `get_logs()` | No |
| `@app.post('/reputation')` | `reputation(request, payload)` | No |
| `@app.get('/cache')` | `cache_stats()` | No |

**Exception Handlers:**
- `StarletteHTTPException` → JSON `{error: ...}` with matched status code (404, 405, etc.)
- Generic `Exception` → JSON `{error: ...}` with 500 status code + logger.error

---

### [features.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/features.py)
**Purpose:** Extracts 17 numeric/binary features from a URL string for ML inference.

**Imports:** `re`, `math`, `tldextract`, `urllib.parse.urlparse`

**Constants:**
- `SUSPICIOUS_TLDS` — Set of 13 suspicious TLDs (`.xyz`, `.top`, etc.)
- `BRAND_NAMES` — List of 12 brand keywords (`paypal`, `amazon`, etc.)

**Functions:**
- `calculate_entropy(url)` → float — Shannon entropy of character frequencies
- `extract_features(url)` → dict — Returns 17 key-value pairs

**Called by:** `app.py:predict_url()`, `train_model.py`, `evaluate.py`, `compare_models.py`

---

### [reputation.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/reputation.py)
**Purpose:** External threat intelligence aggregator.

**Functions:**
- `check_phishtank(url)` → dict — POSTs to PhishTank API
- `check_virustotal(url)` → dict — Queries VirusTotal v3 API (hardcoded API key!)
- `check_domain_age(url)` → dict — WHOIS lookup for domain registration date
- `get_reputation(url)` → dict — Aggregates all three into a reputation score (0–100)

**Called by:** `app.py:/reputation` endpoint

---

### [cache.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/cache.py)
**Purpose:** Redis caching layer with graceful fallback.

**Functions:**
- `get_cache_key(url)` → `phishguard:[MD5]`
- `get_cached(url)` → dict or None
- `set_cached(url, result)` → stores with 1-hour TTL
- `get_cache_stats()` → dict with memory, keys, hits, misses

**Called by:** `app.py` (`/predict` and `/cache` endpoints)

---

### [logger.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/logger.py)
**Purpose:** Dual-output logger (file + stdout).

**Exports:** `logger` — a `logging.Logger` named `'PhishGuard'`

**Called by:** `app.py` (error + info logging)

---

## ML Pipeline Files

### [train_model.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/train_model.py)
**Purpose:** Offline model training pipeline. Loads `data.csv/phishing_site_urls.csv`, extracts features, splits 70/15/15, runs RandomizedSearchCV, saves PKL files, logs to MLflow.

### [evaluate.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/evaluate.py)
**Purpose:** Offline evaluation script. Generates confusion matrix, ROC curve, feature importance plot, and threshold analysis.

### [compare_models.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/compare_models.py)
**Purpose:** Compares Random Forest, Gradient Boosting, and Logistic Regression.

### [mlflow_tracking.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/mlflow_tracking.py)
**Purpose:** MLflow experiment setup and model/param/metric logging.

### [benchmark.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/benchmark.py)
**Purpose:** Latency benchmark against running server for 10 test URLs.

### [test_api.py](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/test_api.py)
**Purpose:** 23-assertion integration test suite. Tests health, safe URLs, phishing URLs, edge cases, analyze, logs, and performance.

---

## Extension Files

### [content.js](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/content.js)
**Purpose:** Main content script injected into Gmail. Scans DOM, runs NLP keyword analysis, sends URLs to backend, injects badges, blocks dangerous clicks, handles graceful degradation when backend is offline.

### [background.js](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/background.js)
**Purpose:** Service worker that initializes `chrome.storage.local` counters on install.

### [popup.js](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/popup.js)
**Purpose:** Reads scan stats from storage and checks backend health.

### [popup.html](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/popup.html)
**Purpose:** Dashboard UI for the extension action popup.

### [styles.css](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/styles.css)
**Purpose:** Badge colors, tooltip positioning, click-blocked link styling.

### [manifest.json](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/manifest.json)
**Purpose:** Chrome Manifest V3 config. Declares permissions, host permissions, content scripts, popup action, background service worker.
