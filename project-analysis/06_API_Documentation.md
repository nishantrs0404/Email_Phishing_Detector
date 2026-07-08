# API Documentation

All endpoints are served by FastAPI on port `5000`. Auto-generated interactive docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## GET `/health`
**Purpose:** Service health check.
**Auth:** None. **Rate Limit:** Default (200/day, 50/hour).
**Response:**
```json
{"status": "running", "threshold": 0.35}
```
**Used by:** `popup.js`, CI pipeline, Railway healthcheck.

---

## POST `/predict`
**Purpose:** Single URL ML prediction.
**Auth:** None. **Rate Limit:** 30/minute per IP.
**Request Model:** `PredictRequest`
```json
{"url": "http://paypal-login-secure.xyz"}
```
**Validation:** If `url` is empty/null → `400 {"error": "No URL provided"}`
**Response (cache miss):**
```json
{
  "url": "http://paypal-login-secure.xyz",
  "prediction": 1,
  "probability": 0.9497,
  "is_phishing": true,
  "threat_level": "DANGEROUS",
  "response_time_ms": 142.1,
  "cached": false
}
```
**Response (cache hit):** Same structure with `"cached": true` and faster `response_time_ms`.
**Used by:** `content.js`

---

## POST `/analyze`
**Purpose:** Batch URL analysis for entire emails.
**Auth:** None. **Rate Limit:** Default.
**Request Model:** `AnalyzeRequest`
```json
{
  "email_text": "verify your account immediately",
  "urls": ["http://paypal-login.xyz", "https://google.com"],
  "sender": "security@paypal-fake.xyz"
}
```
**Validation:** If `urls` is empty → `400 {"error": "No URLs provided"}`
**Response:**
```json
{
  "sender": "security@paypal-fake.xyz",
  "total_urls": 2,
  "threat_count": 1,
  "results": [{...}, {...}],
  "response_time_ms": 285.4
}
```
**Used by:** Available for bulk auditing; `content.js` uses `/predict` per-URL instead.

---

## GET `/logs`
**Purpose:** Retrieve 20 most recent prediction logs.
**Auth:** None. **Rate Limit:** Default.
**Response:**
```json
[
  {"id": 142, "timestamp": "2026-07-08T14:30:11", "url": "...", "prediction": 1, "probability": 0.94, "response_time_ms": 142.1}
]
```

---

## POST `/reputation`
**Purpose:** External threat intelligence lookup (PhishTank + VirusTotal + WHOIS).
**Auth:** None. **Rate Limit:** Default.
**Request Model:** `ReputationRequest`
```json
{"url": "http://paypal-login-secure.xyz"}
```
**Validation:** If `url` is empty/null → `400 {"error": "No URL provided"}`
**Response:**
```json
{
  "phishtank": {"in_database": true, "verified_phish": true, "phish_id": 123456},
  "virustotal": {"malicious_engines": 12, "suspicious_engines": 1, "total_engines": 90, "is_malicious": true, "vt_score": "12/90"},
  "domain_age": {"domain": "paypal-login-secure.xyz", "age_days": 12, "is_new": true},
  "reputation_score": 100,
  "is_dangerous": true
}
```

---

## GET `/cache`
**Purpose:** Redis cache diagnostics.
**Auth:** None. **Rate Limit:** Default.
**Response (connected):**
```json
{"status": "connected", "used_memory": "1.24M", "total_keys": 421, "hits": 1420, "misses": 310}
```
**Response (unavailable):**
```json
{"status": "unavailable"}
```
