from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import joblib, os, sys, time, sqlite3
from datetime import datetime
from reputation import get_reputation
from logger import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cache import get_cached, set_cached, get_cache_stats

sys.path.append(os.path.dirname(__file__))
from features import extract_features

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request Models
class PredictRequest(BaseModel):
    url: Optional[str] = None

class AnalyzeRequest(BaseModel):
    email_text: Optional[str] = ""
    urls: List[str] = Field(default_factory=list)
    sender: Optional[str] = ""

class ReputationRequest(BaseModel):
    url: Optional[str] = None

# Custom Exception Handlers for Flask Parity
@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse({'error': 'Endpoint not found'}, status_code=404)
    elif exc.status_code == 405:
        return JSONResponse({'error': 'Method not allowed'}, status_code=405)
    return JSONResponse({'error': exc.detail}, status_code=exc.status_code)

@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse({'error': str(exc)}, status_code=500)

# Load model
model = joblib.load('model/phishing_model.pkl')
feature_names = joblib.load('model/feature_names.pkl')
THRESHOLD = 0.35
print("Model loaded.")

# Database
os.makedirs('logs', exist_ok=True)

def init_db():
    conn = sqlite3.connect('logs/requests.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        url TEXT,
        prediction INTEGER,
        probability REAL,
        response_time_ms REAL
    )''')
    conn.commit()
    conn.close()

init_db()

def log_request(url, prediction, probability, response_time):
    conn = sqlite3.connect('logs/requests.db')
    conn.execute('INSERT INTO logs VALUES (NULL,?,?,?,?,?)',
        (datetime.now().isoformat(), url, prediction, probability, response_time))
    conn.commit()
    conn.close()

def predict_url(url):
    try:
        url = str(url).strip()
        if len(url) > 2000:
            url = url[:2000]
        if not url.startswith(('http','ftp','www')):
            url = 'http://' + url
        features = extract_features(url)
        values = [list(features.values())]
        prob = model.predict_proba(values)[0][1]
        pred = 1 if prob >= THRESHOLD else 0
        return pred, round(float(prob), 4)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return 0, 0.0

def get_threat_level(probability):
    if probability >= 0.75:   return 'DANGEROUS'
    elif probability >= 0.50: return 'SUSPICIOUS'
    elif probability >= 0.35: return 'LOW_RISK'
    return 'SAFE'

# Routes
@app.get('/health')
def health():
    return {'status': 'running', 'threshold': THRESHOLD}

@app.post('/predict')
@limiter.limit("30/minute")
def predict(request: Request, payload: PredictRequest):
    start = time.time()
    url = payload.url
    if not url:
        return JSONResponse({'error': 'No URL provided'}, status_code=400)

    cached = get_cached(url)
    if cached:
        cached['cached'] = True
        cached['response_time_ms'] = round((time.time()-start)*1000, 2)
        return cached

    pred, prob = predict_url(url)
    ms = round((time.time()-start)*1000, 2)
    log_request(url, pred, prob, ms)
    logger.info(f"PREDICT | {url[:60]} | {get_threat_level(prob)} | {prob} | {ms}ms")

    result = {
        'url': url,
        'prediction': pred,
        'probability': prob,
        'is_phishing': bool(pred == 1),
        'threat_level': get_threat_level(prob),
        'response_time_ms': ms,
        'cached': False
    }
    set_cached(url, result)
    return result

@app.post('/analyze')
def analyze(request: Request, payload: AnalyzeRequest):
    start = time.time()
    email_text = payload.email_text
    urls = payload.urls
    sender = payload.sender
    if not urls:
        return JSONResponse({'error': 'No URLs provided'}, status_code=400)

    results = []
    threat_count = 0
    for url in urls:
        pred, prob = predict_url(url)
        level = get_threat_level(prob)
        if pred == 1: threat_count += 1
        log_request(url, pred, prob, 0)
        logger.info(f"ANALYZE | {url[:60]} | {level} | {prob}")
        results.append({
            'url': url,
            'prediction': pred,
            'probability': prob,
            'threat_level': level,
            'is_phishing': bool(pred == 1)
        })

    ms = round((time.time()-start)*1000, 2)
    return {
        'sender': sender,
        'total_urls': len(urls),
        'threat_count': threat_count,
        'results': results,
        'response_time_ms': ms
    }

@app.get('/logs')
def get_logs():
    conn = sqlite3.connect('logs/requests.db')
    rows = conn.execute(
        'SELECT * FROM logs ORDER BY id DESC LIMIT 20').fetchall()
    conn.close()
    return [{
        'id': r[0], 'timestamp': r[1], 'url': r[2],
        'prediction': r[3], 'probability': r[4],
        'response_time_ms': r[5]
    } for r in rows]

@app.post('/reputation')
def reputation(request: Request, payload: ReputationRequest):
    url = payload.url
    if not url:
        return JSONResponse({'error': 'No URL provided'}, status_code=400)
    result = get_reputation(url)
    return result

@app.get('/cache')
def cache_stats():
    return get_cache_stats()

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run("app:app", host='0.0.0.0', port=port, reload=True)
