# Code Execution Flow

---

## 1. Backend Startup

1. **`python app.py`** → imports `uvicorn`, calls `uvicorn.run("app:app", host='0.0.0.0', port=5000, reload=True)`
2. **Module-level execution in `app.py`:**
   - `FastAPI()` instance created
   - `CORSMiddleware` added (allow all origins)
   - `SlowAPI Limiter` configured (200/day, 50/hour defaults)
   - `RateLimitExceeded` exception handler registered
   - Pydantic request models defined (`PredictRequest`, `AnalyzeRequest`, `ReputationRequest`)
   - Custom exception handlers registered for `StarletteHTTPException` and generic `Exception`
   - **Model loaded:** `joblib.load('model/phishing_model.pkl')` and `joblib.load('model/feature_names.pkl')`
   - **Database initialized:** `os.makedirs('logs')` + `init_db()` creates SQLite table
   - All route handlers registered
3. **`cache.py` module-level:** Redis connection attempted → `REDIS_AVAILABLE` flag set
4. **`logger.py` module-level:** `logs/` directory created, `logging.basicConfig` configured with file + stream handlers

**Production (Docker/Gunicorn):**
`gunicorn -c gunicorn.conf.py app:app` → Gunicorn spawns 2 workers, each using `UvicornWorker` to serve the ASGI FastAPI app.

---

## 2. Extension Initialization

1. **Install event:** `background.js` fires `chrome.runtime.onInstalled` → sets `totalScanned: 0`, `totalThreats: 0`, `scanHistory: []` in `chrome.storage.local`
2. **Gmail page load:** Chrome matches `https://mail.google.com/*` → injects `content.js` + `styles.css` at `document_idle`
3. **`content.js` module-level:** Sets up `MutationObserver` on `document.body` + schedules initial `scanEmail()` after 3 seconds

---

## 3. Email Scanning Flow (When User Opens an Email)

```
Gmail DOM change detected
        │
        ▼
MutationObserver fires → checks for .a3s.aiL (email body container)
        │
        ▼
scanEmail() called after 1s delay
        │
        ├─► getEmailSender() — reads .gD element for sender address
        ├─► analyzeEmailText(emailText) — NLP keyword scan
        │     Returns: { score, triggered[], risk: HIGH/MEDIUM/LOW/NONE }
        ├─► isSuspiciousSender(email) — checks TLD + brand impersonation
        │
        ├─► [If HIGH risk or suspicious sender] → inject warning banner
        │
        ├─► Parse all <a> elements in email body
        │     Filter: must be http*, not mail.google.com, not already scanned
        │     Filter: whitelisted domains → instant SAFE badge
        │
        ▼
For each remaining URL (sequential, 150ms delay):
        │
        ├─► checkUrl(url, element, nlpScore)
        │     │
        │     ├─► fetch POST http://127.0.0.1:5000/predict {url}
        │     │     AbortController timeout: 5 seconds
        │     │
        │     ├─► [Success] Apply hybrid scoring:
        │     │     hybridProb = ML prob + NLP boost (+0.15 if score≥10, +0.08 if score≥5)
        │     │     Map to threat level → addBadge()
        │     │     If DANGEROUS → block clicks with event listener
        │     │
        │     └─► [Failure] Graceful degradation:
        │           If NLP score ≥ 10 → mark SUSPICIOUS (prob 0.6)
        │           Otherwise → silent fail
        │
        ▼
Update chrome.storage.local stats
```

---

## 4. Server-Side `/predict` Flow

```
POST /predict received
        │
        ├─► SlowAPI rate limit check (30/minute per IP)
        ├─► Pydantic validates PredictRequest body
        │
        ├─► Check: url empty? → 400 JSONResponse
        │
        ├─► get_cached(url) — Redis lookup by MD5 hash key
        │     │
        │     └─► [Hit] → return cached dict with cached=True
        │
        ├─► predict_url(url):
        │     ├─► Sanitize (strip, truncate 2000 chars, add http:// if needed)
        │     ├─► extract_features(url) → 17-feature dict
        │     └─► model.predict_proba(values)[0][1] → probability
        │         pred = 1 if prob ≥ 0.35 else 0
        │
        ├─► log_request() → INSERT into SQLite
        ├─► logger.info() → write to log file
        ├─► set_cached(url, result) → Redis SET with 1-hour TTL
        │
        └─► Return JSON dict
```

---

## 5. Shutdown

- **Uvicorn (dev):** `Ctrl+C` → graceful shutdown signal → workers exit
- **Gunicorn (prod):** `SIGTERM` → worker drain → process exit
- SQLite connections are opened/closed per-request (no persistent connection pool)
- Redis connection remains open at module level but is fault-tolerant
