# PhishGuard AI — Project Overview (Post-Migration)

## Purpose
PhishGuard AI is a real-time phishing detection system that protects Gmail users from malicious URLs. It consists of a Chrome browser extension (client) and a Python REST API (server) powered by a Random Forest machine learning classifier trained on 549,000+ URLs.

---

## Features
- Real-time URL scanning inside Gmail emails via MutationObserver
- Random Forest classifier (94.91% ROC-AUC, 17 engineered URL features)
- NLP keyword analysis of email body text (5 weighted categories)
- Hybrid scoring combining ML probability + NLP boost
- 4-tier threat classification: DANGEROUS, SUSPICIOUS, LOW_RISK, SAFE
- Click interception and blocking for DANGEROUS links
- External threat intelligence (VirusTotal API, PhishTank, WHOIS domain age)
- Redis caching layer (1-hour TTL) with graceful fallback
- SQLite audit logging for all predictions
- Live popup dashboard showing scan statistics
- Auto-generated OpenAPI/Swagger documentation at `/docs`

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | FastAPI (ASGI), Uvicorn, Gunicorn |
| **Machine Learning** | scikit-learn (Random Forest), Pandas, NumPy, Joblib |
| **Experiment Tracking** | MLflow |
| **Databases** | SQLite (audit logs), Redis (prediction cache) |
| **Rate Limiting** | SlowAPI (based on `limits` library) |
| **Request Validation** | Pydantic v2 (built into FastAPI) |
| **Threat Intelligence** | VirusTotal API v3, PhishTank API, python-whois |
| **Browser Extension** | JavaScript ES6, Chrome Manifest V3 |
| **CI/CD** | GitHub Actions (lint → test → docker build) |
| **Deployment** | Docker, Docker Compose, Railway |

---

## Architecture

```
Chrome Extension (Gmail)
        |
        | URL + email text (HTTP POST)
        v
FastAPI REST API (port 5000, Uvicorn)
        |
   -----+-----
   |         |
Feature    Redis
Extractor  Cache
   |         |
   -----+-----
        |
        v
Random Forest Model
(549,000 URLs, AUC 0.9491)
        |
        v
Threat Level + Probability
        |
        v
Visual Badge in Gmail
```

---

## Folder Structure
```
phishing-detector-main/
├── .github/workflows/ci.yml      # GitHub Actions CI/CD pipeline
├── backend/
│   ├── app.py                     # FastAPI application (endpoints, models, error handlers)
│   ├── features.py                # URL feature extraction (17 features)
│   ├── reputation.py              # PhishTank, VirusTotal, WHOIS integration
│   ├── cache.py                   # Redis caching layer
│   ├── logger.py                  # File + console logger
│   ├── train_model.py             # Model training pipeline
│   ├── evaluate.py                # Performance evaluation with plots
│   ├── compare_models.py          # RF vs GB vs LR comparison
│   ├── benchmark.py               # Latency benchmarking
│   ├── test_api.py                # 23-test API integration suite
│   ├── mlflow_tracking.py         # MLflow experiment logging
│   ├── gunicorn.conf.py           # Gunicorn + UvicornWorker config
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Multi-stage Docker build
│   ├── model_card.md              # Model documentation
│   ├── model/                     # Serialized model binaries (.pkl)
│   ├── logs/                      # SQLite DB + runtime logs
│   └── mlflow/ & mlruns/          # MLflow tracking data
├── extension/
│   ├── manifest.json              # Chrome MV3 configuration
│   ├── content.js                 # Gmail DOM scanner + NLP + badges
│   ├── background.js              # Service worker (stats init)
│   ├── popup.html                 # Dashboard UI
│   ├── popup.js                   # Dashboard logic + health check
│   ├── styles.css                 # Badge/tooltip/block styles
│   └── icons/                     # Extension icons
├── docker-compose.yml             # API + Redis container orchestration
├── railway.json                   # Railway deployment config
└── README.md                      # Project documentation
```

---

## Execution Flow Summary
1. Extension installs → `background.js` initializes storage counters
2. User opens Gmail → `content.js` sets up MutationObserver on `document.body`
3. Email opened → DOM change detected → `scanEmail()` triggered
4. Email body parsed → NLP keyword analysis + sender validation
5. Links extracted → whitelisted domains get instant SAFE badge
6. Remaining URLs → sequential `POST /predict` to FastAPI backend
7. Backend: Redis cache check → feature extraction → RF model inference → SQLite log → Redis cache set
8. Extension receives response → hybrid score (ML prob + NLP boost) → badge injection + optional click blocking
9. Popup dashboard reads `chrome.storage.local` for statistics and pings `/health` for backend status
