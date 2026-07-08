# Performance Analysis

---

## Latency Breakdown

| Operation | Typical Latency | Location |
| :--- | :--- | :--- |
| Feature extraction | ~15ms | `features.py:extract_features()` |
| RF model inference | ~20ms | `app.py:predict_url()` |
| SQLite INSERT | ~5ms | `app.py:log_request()` |
| Redis GET (cache hit) | ~1.5ms | `cache.py:get_cached()` |
| Redis SET | ~2ms | `cache.py:set_cached()` |
| **Total `/predict` (cache miss)** | **~40ms** | |
| **Total `/predict` (cache hit)** | **~2ms** | |
| PhishTank API | ~1.2s | `reputation.py:check_phishtank()` |
| VirusTotal API | ~800ms | `reputation.py:check_virustotal()` |
| WHOIS lookup | ~2.5s | `reputation.py:check_domain_age()` |
| **Total `/reputation`** | **~4.5s** | Sequential calls |

---

## Bottlenecks

### 1. Sequential Reputation Checks
`get_reputation()` calls PhishTank, VirusTotal, and WHOIS sequentially. Total latency = sum of all three.
**Fix:** Use `concurrent.futures.ThreadPoolExecutor` to run in parallel.

### 2. Sequential Link Scanning (Extension)
`content.js` scans URLs one-by-one with 150ms delay between requests. 10 links = ~2.5 seconds.
**Fix:** Use `Promise.all()` for parallel scanning.

### 3. SQLite Connection Per-Request
Each prediction opens a new SQLite connection, writes, commits, closes. Under high concurrency this creates file lock contention.
**Fix:** Use a connection pool or WAL mode (`PRAGMA journal_mode=WAL`).

### 4. Synchronous Endpoints on ASGI Server
All endpoints use synchronous `def` (not `async def`). FastAPI runs these in a thread pool, which is correct behavior for CPU-bound and blocking I/O operations (model inference, sqlite3). Converting to `async def` without async drivers would actually block the event loop and reduce performance.

---

## Memory Usage
- Random Forest model (~45MB RAM with 200 estimators, depth 30)
- Redis: Docker-limited to 256MB with LRU eviction
- SQLite: Negligible in-memory footprint (file-backed)

---

## Caching Effectiveness
- **Hit rate:** Depends on email link diversity. Corporate emails with recurring URLs will see high hit rates.
- **TTL:** 1 hour. Reasonable for URL classification (phishing URLs rarely change status within an hour).
- **Key strategy:** MD5 hash of full URL. Query parameter differences create distinct cache keys (correct behavior for security).
