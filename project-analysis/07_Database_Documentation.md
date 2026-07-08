# Database Documentation

---

## SQLite — Audit Logging

**File:** `backend/logs/requests.db`
**Driver:** Python `sqlite3` (stdlib, no ORM)
**Created by:** `init_db()` in `app.py` at module load time

### Schema
```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    url TEXT,
    prediction INTEGER,
    probability REAL,
    response_time_ms REAL
);
```

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Auto-incrementing PK |
| `timestamp` | TEXT | ISO 8601 datetime string |
| `url` | TEXT | Scanned URL (up to 2000 chars) |
| `prediction` | INTEGER | `1` = phishing, `0` = safe |
| `probability` | REAL | Model confidence (0.0–1.0) |
| `response_time_ms` | REAL | End-to-end latency in ms |

### Queries Used
| Query | Location | Purpose |
| :--- | :--- | :--- |
| `INSERT INTO logs VALUES (NULL,?,?,?,?,?)` | `app.py:log_request()` | Log every prediction |
| `SELECT * FROM logs ORDER BY id DESC LIMIT 20` | `app.py:get_logs()` | Retrieve recent logs |

### Connection Pattern
Connections are opened and closed per-request (no pooling). This is safe for SQLite's file-level locking but could become a bottleneck under high concurrency.

### Indexes
No explicit indexes beyond the `id` PRIMARY KEY. The `ORDER BY id DESC LIMIT 20` query is efficient because SQLite uses the PK index.

---

## Redis — Prediction Cache

**Connection:** `localhost:6379`, database 0, 2-second timeout
**Driver:** `redis-py`
**TTL:** 3600 seconds (1 hour)

### Key Format
```
phishguard:[MD5_HASH_OF_URL]
```

### Value Format
JSON string:
```json
{
  "url": "...",
  "prediction": 1,
  "probability": 0.9497,
  "is_phishing": true,
  "threat_level": "DANGEROUS",
  "response_time_ms": 142.1,
  "cached": false
}
```

### Graceful Fallback
If Redis is unreachable at startup, `REDIS_AVAILABLE` is set to `False`. All cache operations become no-ops, and the app runs without caching.

### Docker Redis Config
```
redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```
LRU eviction ensures the cache stays within memory bounds.
