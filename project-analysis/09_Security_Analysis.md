# Security Analysis

---

## Authentication & Authorization
**Current state:** No authentication on any endpoint. Anyone with network access to port 5000 can query all endpoints.

---

## Rate Limiting
- **Default:** 200 requests/day, 50 requests/hour per IP (via `slowapi`).
- **`/predict`:** 30 requests/minute per IP.
- **Implementation:** `slowapi.Limiter` with `get_remote_address` key function. `RateLimitExceeded` exception handler registered globally.

---

## Input Validation
- **Pydantic models** enforce JSON schema on POST endpoints (`PredictRequest`, `AnalyzeRequest`, `ReputationRequest`). Invalid JSON structure returns FastAPI's default 422 response.
- **Manual validation** checks for empty `url` / `urls` fields and returns 400 with custom error messages (preserving pre-migration behavior).
- **URL length truncation:** URLs > 2000 characters are truncated in `predict_url()`.

---

## SQL Injection Protection
All SQLite queries use **parameterized statements** (`?` placeholders):
```python
conn.execute('INSERT INTO logs VALUES (NULL,?,?,?,?,?)', (...))
```

---

## CORS Policy
```python
CORSMiddleware(allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```
> [!WARNING]
> **Wildcard CORS** allows any website to call the API. In production, restrict to `chrome-extension://<ID>`.

---

## Vulnerabilities

### 1. Hardcoded VirusTotal API Key (HIGH)
**Location:** [reputation.py:L5](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/reputation.py#L5)
```python
VIRUSTOTAL_API_KEY = "a72a2ff976f49a60c37232a37ff2facaf26302a2872e8c68999f945d16519d8f"
```
**Fix:** `os.environ.get("VIRUSTOTAL_API_KEY", "")`

### 2. Plaintext URL Logging (MEDIUM)
URLs are stored in plaintext in SQLite. Sensitive tokens in query parameters are persisted.
**Fix:** Strip query parameters or hash URLs before logging.

### 3. Open CORS (MEDIUM)
Any website can query `/predict`, `/logs`, etc.
**Fix:** Restrict `allow_origins` to the extension's Chrome ID.

### 4. Client-Side Security Enforcement (LOW)
Click blocking is purely JavaScript — bypassable via DevTools. Acceptable since the goal is protecting against accidental clicks, not enforcing access control.

### 5. No HTTPS Enforcement (LOW)
Backend runs on HTTP. Acceptable for `localhost` dev but should use TLS in production (Railway provides HTTPS by default).
