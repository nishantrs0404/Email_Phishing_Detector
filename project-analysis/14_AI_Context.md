# AI Context — Complete Knowledge Base

This document contains everything an AI agent needs to understand and safely modify this project.

---

## Project Identity
**Name:** PhishGuard AI
**Type:** Real-time phishing email detector (Chrome extension + ML backend)
**Framework:** FastAPI (ASGI) — migrated from Flask in July 2026
**Language:** Python 3.11 (backend), JavaScript ES6 (extension)
**Status:** Production-ready

---

## Architecture
- **Client-Server.** The Chrome extension (Manifest V3) runs inside Gmail and communicates with a Python FastAPI REST API over HTTP on port 5000.
- **ML Model:** scikit-learn Random Forest Classifier. 17 URL features. Trained on 549k URLs. ROC-AUC 0.9491.
- **Caching:** Redis (1-hour TTL, MD5 key hashing, graceful fallback if offline).
- **Logging:** SQLite (audit trail of every prediction), Python `logging` (file + console).
- **Rate Limiting:** SlowAPI (200/day, 50/hour defaults; 30/minute on `/predict`).
- **Request Validation:** Pydantic models for all POST endpoints.
- **CORS:** Wildcard `*` (should be restricted in production).
- **Deployment:** Docker + Docker Compose + Railway.app. Gunicorn with UvicornWorker.

---

## Critical Files

| File | Role | Risk Level |
| :--- | :--- | :--- |
| `backend/app.py` | FastAPI app, all endpoints, model loading, DB init | **Critical** — changes here affect everything |
| `backend/features.py` | 17-feature extraction | **Critical** — changes require model retraining |
| `backend/model/phishing_model.pkl` | Serialized RF model | **Critical** — must match feature count/order |
| `backend/model/feature_names.pkl` | Feature name list | **Critical** — must match features.py output |
| `extension/content.js` | Gmail scanner, NLP, badges, click blocking | **Critical** — changes affect user experience |
| `backend/reputation.py` | External API integrations | **High** — contains hardcoded API key |
| `backend/cache.py` | Redis caching | **Medium** |
| `extension/manifest.json` | Extension permissions | **High** — incorrect permissions = broken extension |

---

## Business Logic Formulas

### Threat Classification
```
P ≥ 0.75  →  DANGEROUS  (click blocked, red badge)
P ≥ 0.50  →  SUSPICIOUS (orange badge)
P ≥ 0.35  →  LOW_RISK   (yellow badge)
P < 0.35  →  SAFE       (green badge)
```

### Hybrid Scoring (client-side only)
```
if NLP_score ≥ 10:  final_prob = min(1.0, ML_prob + 0.15)
elif NLP_score ≥ 5: final_prob = min(1.0, ML_prob + 0.08)
else:               final_prob = ML_prob
```

### Reputation Score (backend only)
```
+40 if PhishTank verified phish
+40 if VirusTotal is_malicious (≥3 engines)
+10 if VirusTotal ≥1 malicious engine
+20 if domain age < 180 days
Total ≥ 40 → is_dangerous
```

---

## Naming Conventions
- **Python:** snake_case for functions and variables, PascalCase for Pydantic models
- **JavaScript:** camelCase for functions and variables, UPPER_CASE for constants
- **CSS:** BEM-like naming: `.phishing-badge`, `.phishing-dangerous`, `.phishing-tooltip`
- **API paths:** Lowercase, no trailing slashes: `/predict`, `/analyze`, `/reputation`
- **Cache keys:** `phishguard:[MD5_HASH]`

---

## Coding Style
- **Backend:** Compact PEP 8 with 120-char line limit. Inline conditionals common. Bare `except:` used in several places (a known code smell).
- **Frontend:** Direct DOM manipulation, no frameworks. `MutationObserver` pattern for dynamic content. `chrome.storage.local` for persistence.
- **Error handling:** Custom exception handlers produce `{"error": "message"}` JSON for all error responses. No stack traces exposed to clients.

---

## Known Issues
1. **Hardcoded VirusTotal API key** in `reputation.py:L5` — HIGH security risk
2. **Wildcard CORS** in `app.py:L24` — allows any origin
3. **Sequential reputation checks** — 4.5s latency on `/reputation`
4. **Sequential URL scanning** in `content.js` — slow for emails with many links
5. **Bare `except:` clauses** in features.py, cache.py, reputation.py — swallow all exceptions
6. **Unused variable** `domain_full` in `features.py:L52`
7. **Duplicate import** of `roc_curve, auc` in `train_model.py` (L8 and L89)
8. **README.md** still references Flask in multiple locations
9. **`urlparse` imported but never used** in `features.py:L4`

---

## Safe Modification Guidelines

1. **Never change `features.py` without retraining the model.** The model expects exactly 17 features in a specific order.
2. **Never change Pydantic models without updating `test_api.py`.** Tests validate response shapes.
3. **Never add `async def` without async I/O drivers.** Synchronous `sqlite3` and `requests` will block the event loop.
4. **Never delete `logs/requests.db` in production** — it contains the audit trail.
5. **Always update the CI dummy model** in `ci.yml` if feature count changes (currently hardcoded to 17).
6. **The extension hardcodes `127.0.0.1:5000`** — changing the backend port requires updating `content.js:L3` and `popup.js:L8`.

---

## Future Extension Points
1. **Add `/feedback` endpoint** for user-submitted false positive/negative reports → feed into model retraining
2. **VirusTotal integration** already implemented but could be enriched with submission polling
3. **Domain age scoring** already implemented — could be integrated into the main prediction pipeline (not just `/reputation`)
4. **FastAPI `lifespan` events** — use for model loading and DB initialization instead of module-level code
5. **Pydantic response models** — would enable compile-time response validation and richer OpenAPI docs
6. **Async refactor** — migrate to `httpx.AsyncClient` + `aiosqlite` + `redis.asyncio` for full async chain
7. **WebSocket endpoint** — push real-time scan results to the extension popup dashboard
