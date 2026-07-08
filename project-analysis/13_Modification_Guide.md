# Modification Guide

How to safely modify PhishGuard AI without breaking existing functionality.

---

## 1. Adding a New API Endpoint

1. **Define Pydantic request model** (if POST) in `app.py`:
   ```python
   class MyRequest(BaseModel):
       field: str
   ```
2. **Add route handler:**
   ```python
   @app.post('/my-endpoint')
   def my_endpoint(request: Request, payload: MyRequest):
       return {"result": "ok"}
   ```
3. **Update `test_api.py`** with new test assertions.
4. **Verify:** Run `python test_api.py` and check `/docs` for Swagger entry.

---

## 2. Changing the ML Model

1. **Modify** `train_model.py` with new classifier or hyperparameters.
2. **Run** `python train_model.py` — saves new `.pkl` files to `model/`.
3. **Restart** the server — `app.py` loads `model/phishing_model.pkl` at startup.
4. **Important:** If you add/remove features in `features.py`, you **must retrain** the model. The feature count and order must match exactly.

---

## 3. Adding a New URL Feature

1. Add calculation in `features.py:extract_features()`:
   ```python
   features['my_new_feature'] = 1 if condition else 0
   ```
2. **Retrain the model:** `python train_model.py` (this regenerates both `.pkl` files).
3. **Update `model_card.md`** to document the new feature.
4. **Update CI dummy model** in `.github/workflows/ci.yml` — change `17` to `18` in the numpy array shape and add the feature name to the list.

---

## 4. Modifying the SQLite Schema

1. Update `init_db()` in `app.py` with the new column.
2. Update `log_request()` INSERT statement.
3. Update `get_logs()` SELECT and response dict.
4. **Delete** existing `logs/requests.db` (SQLite doesn't support easy schema migration) or run a manual `ALTER TABLE`.
5. Update `test_api.py` assertions if the `/logs` response shape changes.

---

## 5. Changing Cache TTL

Edit `cache.py:L16`:
```python
CACHE_TTL = 86400  # 24 hours instead of 1 hour
```

---

## 6. Modifying the Chrome Extension

### Adding to the Whitelist
Edit `content.js:WHITELIST` Set:
```javascript
const WHITELIST = new Set([..., 'newtrusted.com']);
```

### Adding NLP Keywords
Edit `content.js:PHISHING_KEYWORDS`:
```javascript
newcategory: { words: ['new', 'keyword'], weight: 3 }
```

### Changing Badge Appearance
Edit `styles.css` for colors, `content.js:addBadge()` for labels.

---

## 7. Updating Dependencies

1. Edit `requirements.txt` with new versions.
2. Run `pip install -r requirements.txt`.
3. Test: `python test_api.py`.
4. If changing Pydantic major version, verify all request models still parse correctly.
5. Rebuild Docker: `docker-compose build`.

---

## 8. Converting to Async Endpoints

Only convert to `async def` if you also switch to async I/O drivers:
- SQLite → `aiosqlite`
- Redis → `redis.asyncio`
- HTTP → `httpx.AsyncClient` (in `reputation.py`)

**Do NOT** simply change `def` to `async def` while keeping synchronous `sqlite3` and `requests` calls — this will block the event loop and severely degrade performance.
