# Improvement Suggestions

---

## 1. Security (High Priority)

### Move API Key to Environment Variable
**File:** [reputation.py:L5](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/reputation.py#L5)
```python
# Current (DANGEROUS):
VIRUSTOTAL_API_KEY = "a72a2ff976f49a60..."
# Fix:
VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")
```

### Restrict CORS Origins
**File:** [app.py:L22-28](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/app.py#L22-L28)
```python
allow_origins=["chrome-extension://<YOUR_EXTENSION_ID>"]
```

---

## 2. Performance

### Parallel Reputation Checks
**File:** [reputation.py:L86](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/reputation.py#L86)
Use `concurrent.futures.ThreadPoolExecutor` to run PhishTank, VirusTotal, and WHOIS in parallel (reduces ~4.5s → ~2.5s).

### Parallel Link Scanning
**File:** [content.js:L259](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/extension/content.js#L259)
Replace sequential loop with `Promise.all()` for concurrent URL checks.

### SQLite WAL Mode
Add `PRAGMA journal_mode=WAL` in `init_db()` for better concurrent read/write performance.

---

## 3. Code Quality

### Consolidate Threat Level Logic
Threat level mapping exists in both `app.py:get_threat_level()` and `content.js:checkUrl()`. The extension should rely solely on the backend's `threat_level` field, with the NLP boost applied as a separate modifier. This eliminates duplicate business logic.

### Remove Duplicate Imports
[train_model.py:L8](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/train_model.py#L8) and [train_model.py:L89](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/train_model.py#L89) both import `roc_curve` and `auc`.

### Unused Variable
[features.py:L52](file:///c:/Users/Nishant%20Raushan/OneDrive/ドキュメント/Projects/phishing-detector-main/backend/features.py#L52): `domain_full` is assigned but never used.

### Bare `except` Clauses
Multiple files use bare `except:` without specifying exception types (`features.py:L55`, `cache.py:L29,39`, `reputation.py:L19,82`). These silently swallow all errors including `KeyboardInterrupt`.

---

## 4. Testing

### Add Unit Tests for Feature Extraction
Create `test_features.py` to verify entropy values, feature counts, and edge cases without needing a running server.

### Add Pydantic Response Models
Define Pydantic response models in `app.py` to enable compile-time validation of response shapes and enhance the auto-generated OpenAPI documentation.

---

## 5. Scalability

### Use FastAPI Startup/Shutdown Events
Replace module-level `init_db()` and `joblib.load()` with FastAPI `@app.on_event("startup")` or `lifespan` context manager for cleaner lifecycle management.

### Connection Pooling for SQLite
Consider using `aiosqlite` or a connection pool wrapper if moving to async endpoints in the future.

---

## 6. Documentation

### Update README.md
The README still references Flask in several places. Update to reflect the current FastAPI stack.
