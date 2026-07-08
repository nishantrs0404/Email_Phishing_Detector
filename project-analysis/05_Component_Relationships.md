# Component Relationships

---

## System Architecture Diagram

```mermaid
graph TD
    subgraph Browser ["Chrome Extension"]
        A[content.js] -- DOM mutations --> B["Gmail DOM (.a3s.aiL)"]
        A -- Read/Write --> C[(chrome.storage.local)]
        D[popup.js] -- Read Stats --> C
        D -- Dashboard UI --> E[popup.html]
        F[background.js] -- Init storage --> C
    end

    subgraph Backend ["FastAPI Backend (Uvicorn)"]
        G[app.py] -- Init DB --> H[(SQLite requests.db)]
        G -- Load Model --> I[Random Forest .pkl]
        G -- Routing --> K{Endpoints}
        K -- /predict --> L[features.py]
        K -- /reputation --> M[reputation.py]
        K -- Cache check --> N[cache.py]
        G -- Logging --> O[logger.py]
    end

    subgraph External ["External Services"]
        P[VirusTotal API]
        Q[PhishTank API]
        R[WHOIS Servers]
    end

    S[(Redis)]

    A -- HTTP POST /predict --> K
    D -- HTTP GET /health --> K
    N -- Get/Set --> S
    M --> P
    M --> Q
    M --> R
```

---

## Backend Internal Dependency Graph

```mermaid
graph LR
    APP[app.py] --> FEAT[features.py]
    APP --> REP[reputation.py]
    APP --> CACHE[cache.py]
    APP --> LOG[logger.py]
    
    TRAIN[train_model.py] --> FEAT
    TRAIN --> MLF[mlflow_tracking.py]
    
    EVAL[evaluate.py] --> FEAT
    COMP[compare_models.py] --> FEAT
    
    BENCH[benchmark.py] -.HTTP.-> APP
    TEST[test_api.py] -.HTTP.-> APP
```

---

## Data Flow: Predict Request

```mermaid
sequenceDiagram
    autonumber
    participant Ext as content.js
    participant API as app.py (FastAPI)
    participant Cache as Redis
    participant ML as Random Forest
    participant DB as SQLite

    Ext->>API: POST /predict {url}
    API->>API: SlowAPI rate limit check
    API->>API: Pydantic validation
    API->>Cache: get_cached(url)
    alt Cache Hit
        Cache-->>API: cached result
        API-->>Ext: JSON (cached=true)
    else Cache Miss
        API->>API: extract_features(url)
        API->>ML: predict_proba(features)
        ML-->>API: probability
        API->>DB: log_request()
        API->>Cache: set_cached(url, result, TTL=3600)
        API-->>Ext: JSON (cached=false)
    end
    Ext->>Ext: Apply NLP hybrid boost
    Ext->>Ext: Inject badge into DOM
```

---

## Key Interfaces

| Producer | Consumer | Mechanism |
| :--- | :--- | :--- |
| `content.js` | `app.py` | HTTP POST to `127.0.0.1:5000/predict` |
| `popup.js` | `app.py` | HTTP GET to `127.0.0.1:5000/health` |
| `app.py` | `features.py` | Direct Python function call |
| `app.py` | `cache.py` | Direct Python function call |
| `app.py` | `reputation.py` | Direct Python function call |
| `app.py` | `logger.py` | Direct Python `logger.info/error` |
| `app.py` | SQLite | `sqlite3.connect()` per request |
| `cache.py` | Redis | `redis.Redis()` persistent connection |
| `reputation.py` | VirusTotal | HTTP GET/POST via `requests` library |
| `reputation.py` | PhishTank | HTTP POST via `requests` library |
| `reputation.py` | WHOIS | TCP via `python-whois` library |
