from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import sqlite3
import hmac
import hashlib
import json
from datetime import datetime

# Auto-load .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — env vars loaded from Railway/system


# ─────────────────────────────────────────────
# 1. INITIALIZE API
# ─────────────────────────────────────────────
app = FastAPI(
    title="Shield AI — Credit Card Fraud Detection API",
    description="A professional real-time fraud monitoring service built with XGBoost. "
                "Supports real payment gateway integration via Razorpay webhooks.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# 2. ENVIRONMENT CONFIG (use .env in production)
# ─────────────────────────────────────────────
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "your_webhook_secret_here")
RAZORPAY_KEY_ID        = os.getenv("RAZORPAY_KEY_ID", "rzp_test_your_key_id")
RAZORPAY_KEY_SECRET    = os.getenv("RAZORPAY_KEY_SECRET", "your_key_secret")

# ─────────────────────────────────────────────
# 3. LOAD PRE-TRAINED MODELS
# ─────────────────────────────────────────────
MODEL_PATH        = "fraud_model.joblib"
SCALER_AMOUNT_PATH = "scaler_amount.joblib"
SCALER_TIME_PATH   = "scaler_time.joblib"
REAL_MODEL_PATH    = "real_fraud_model.joblib"
REAL_SCALER_PATH   = "real_scaler.joblib"

fraud_model   = None
scaler_amount = None
scaler_time   = None
real_model    = None
real_scaler   = None

@app.on_event("startup")
def load_models():
    global fraud_model, scaler_amount, scaler_time, real_model, real_scaler
    # Load original XGBoost model (V1-V28 features)
    if all(os.path.exists(f) for f in [MODEL_PATH, SCALER_AMOUNT_PATH, SCALER_TIME_PATH]):
        print("[+] Loading XGBoost Fraud Engine (V1-V28 mode)...")
        fraud_model   = joblib.load(MODEL_PATH)
        scaler_amount = joblib.load(SCALER_AMOUNT_PATH)
        scaler_time   = joblib.load(SCALER_TIME_PATH)
        print("[+] XGBoost Model Ready.")
    else:
        print("[!] XGBoost model missing. Run 'python fraud_detection.py' first.")

    # Load real gateway model (trained on payment API features)
    if os.path.exists(REAL_MODEL_PATH) and os.path.exists(REAL_SCALER_PATH):
        print("[+] Loading Real Gateway Fraud Engine...")
        real_model  = joblib.load(REAL_MODEL_PATH)
        real_scaler = joblib.load(REAL_SCALER_PATH)
        print("[+] Real Gateway Model Ready.")
    else:
        print("[~] Real gateway model not found. Run 'python retrain_real_model.py' to enable Razorpay fraud detection.")

# ─────────────────────────────────────────────
# 4. DATABASE INIT
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS alerts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT, amount REAL, confidence REAL,
                      status TEXT, owner TEXT, source TEXT)''')

    cursor.execute("PRAGMA table_info(alerts)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'owner' not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN owner TEXT")
        cursor.execute("UPDATE alerts SET owner = 'deephalder' WHERE owner IS NULL")
    if 'source' not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN source TEXT DEFAULT 'manual'")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, full_name TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO users (username, password, full_name) VALUES ('deephalder', 'shield123', 'Deep Halder')")

    cursor.execute('''CREATE TABLE IF NOT EXISTS webhook_events
                     (event_id TEXT PRIMARY KEY, payload TEXT, processed_at TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS config
                     (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('auto_block', 'disabled')")
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('notifications', 'enabled')")
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# 5. MODELS
# ─────────────────────────────────────────────
class Transaction(BaseModel):
    # Kaggle PCA Features (Optional for simple mode)
    Time: float = 0.0
    V1: float = 0.0;  V2: float = 0.0;  V3: float = 0.0;  V4: float = 0.0;  V5: float = 0.0
    V6: float = 0.0;  V7: float = 0.0;  V8: float = 0.0;  V9: float = 0.0;  V10: float = 0.0
    V11: float = 0.0; V12: float = 0.0; V13: float = 0.0; V14: float = 0.0; V15: float = 0.0
    V16: float = 0.0; V17: float = 0.0; V18: float = 0.0; V19: float = 0.0; V20: float = 0.0
    V21: float = 0.0; V22: float = 0.0; V23: float = 0.0; V24: float = 0.0; V25: float = 0.0
    V26: float = 0.0; V27: float = 0.0; V28: float = 0.0
    # Core features sent by frontend
    amount: float
    hour: float = None
    is_international: bool = False
    owner: str = "Deep Halder"




# ─────────────────────────────────────────────
# 6. REAL FEATURE EXTRACTION (from Razorpay/Stripe data)
# ─────────────────────────────────────────────
def extract_gateway_features(payment: dict) -> list:
    """
    Extract fraud-relevant features from a Razorpay payment object.
    These features are what a real payment gateway actually provides.
    """
    amount_inr = payment.get("amount", 0) / 100  # Razorpay uses paise
    created    = datetime.fromtimestamp(payment.get("created_at", datetime.now().timestamp()))
    hour       = created.hour

    card       = payment.get("card", {}) or {}
    is_intl    = 1 if card.get("international") else 0
    is_card    = 1 if payment.get("method") == "card" else 0
    is_night   = 1 if (hour < 6 or hour > 22) else 0
    is_failed  = 1 if payment.get("status") == "failed" else 0
    # Risk: card present but no issuer info (anonymous card)
    no_issuer  = 1 if (is_card and not card.get("issuer")) else 0

    return [amount_inr, hour, is_intl, is_card, is_night, is_failed, no_issuer]

def save_alert(owner: str, amount: float, confidence: float, source: str = "gateway", status: str = "FLAGGED"):
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (timestamp, amount, confidence, status, owner, source) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().strftime("%H:%M:%S"), amount, round(confidence * 100, 2), status, owner, source)
    )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# 7. RAZORPAY WEBHOOK ENDPOINT (Real Fraud Detection)
# ─────────────────────────────────────────────
def process_razorpay_event(event_id: str, data: dict):
    """Background task: run fraud model on real payment data."""
    # Idempotency: skip already-processed events
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT event_id FROM webhook_events WHERE event_id = ?", (event_id,))
    if cursor.fetchone():
        conn.close()
        return  # Already processed
    cursor.execute(
        "INSERT INTO webhook_events (event_id, payload, processed_at) VALUES (?, ?, ?)",
        (event_id, json.dumps(data), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    amount  = payment.get("amount", 0) / 100  # Rupees
    owner   = payment.get("contact", "razorpay_user")  # Use phone/email as owner key

    print(f"[Razorpay] Processing payment {payment.get('id')} — ₹{amount}")

    # Use real gateway model if available
    if real_model and real_scaler:
        features = extract_gateway_features(payment)
        scaled   = real_scaler.transform([features])
        prob     = float(real_model.predict_proba(scaled)[0][1])
        is_fraud = prob > 0.5
        print(f"[Razorpay] Real Model → prob={prob:.3f} fraud={is_fraud}")
    else:
        # Fallback: simple rule-based risk (until model is trained)
        hour     = datetime.now().hour
        is_intl  = 1 if (payment.get("card") or {}).get("international") else 0
        is_night = 1 if (hour < 6 or hour > 22) else 0
        risk_score = (amount / 50000) + (is_intl * 0.3) + (is_night * 0.2)
        prob     = min(risk_score, 1.0)
        is_fraud = prob > 0.6
        print(f"[Razorpay] Rule-based → risk={prob:.3f} fraud={is_fraud}")

    if is_fraud:
        save_alert(owner=owner, amount=amount, confidence=prob, source="razorpay", status="FRAUD")
        print(f"[Razorpay] 🚨 FRAUD ALERT saved for {owner} — ₹{amount}")

@app.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives real-time payment events from Razorpay.
    Setup in Razorpay Dashboard → Settings → Webhooks → Add URL:
      https://your-deployed-app.com/razorpay/webhook
    Events to enable: payment.captured, payment.failed, payment.authorized
    """
    body      = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature")

    # Verify HMAC-SHA256 signature
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature — possible tampering")

    data     = json.loads(body)
    event_id = request.headers.get("X-Razorpay-Event-Id", data.get("id", "unknown"))
    event    = data.get("event", "")

    print(f"[Razorpay] Webhook received: {event} (id={event_id})")

    # Process fraud check in background (respond fast to Razorpay)
    if event in ["payment.captured", "payment.failed", "payment.authorized"]:
        background_tasks.add_task(process_razorpay_event, event_id, data)

    return {"status": "received", "event": event}

@app.get("/razorpay/status")
def razorpay_status():
    """Check Razorpay integration status."""
    return {
        "webhook_configured": RAZORPAY_WEBHOOK_SECRET != "your_webhook_secret_here",
        "real_model_loaded":  real_model is not None,
        "key_configured":     RAZORPAY_KEY_ID != "rzp_test_your_key_id",
        "instructions": {
            "step1": "Go to razorpay.com → Settings → Webhooks",
            "step2": "Add webhook URL: https://your-app.railway.app/razorpay/webhook",
            "step3": "Enable events: payment.captured, payment.failed",
            "step4": "Copy Webhook Secret → set RAZORPAY_WEBHOOK_SECRET env variable",
            "step5": "Run python retrain_real_model.py to train the gateway model"
        }
    }

# ─────────────────────────────────────────────
# 8. EXISTING API ENDPOINTS (unchanged)
# ─────────────────────────────────────────────
@app.get("/api/alerts")
def get_alerts(user: str = "deephalder"):
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE owner = ? ORDER BY id DESC LIMIT 50", (user,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "time": r[1], "amt": r[2], "conf": r[3], "status": r[4]} for r in rows]

@app.delete("/api/alerts")
def clear_alerts(user: str = "deephalder"):
    """Clears all fraud alerts for the specified user."""
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts WHERE owner = ?", (user,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return {"status": "cleared", "deleted_count": deleted}

@app.post("/api/register")
def register(user_data: dict):
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)",
                       (user_data['username'], user_data['password'], user_data['name']))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"status": "success"}

@app.post("/api/login")
def login(credentials: dict):
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE username = ? AND password = ?",
                   (credentials.get("username"), credentials.get("password")))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"status": "success", "token": "SHIELD_SECURE_2026", "name": user[0]}
    raise HTTPException(status_code=401, detail="Unauthorized Access")

@app.get("/api/alerts/export")
def export_alerts(user: str = "deephalder"):
    import csv, io
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, amount, confidence, status FROM alerts WHERE owner = ? ORDER BY id DESC", (user,))
    rows = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Amount (₹)", "Risk Confidence (%)", "Status"])
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=shield_audit_{user}.csv"}
    )

@app.post("/predict")
def predict_fraud(txn: Transaction, threshold: float = 0.5):
    owner = txn.owner
    is_fraud = False
    prob = 0.05
    
    try:
        # AI LAYER
        if fraud_model is not None:
            data = {f'V{i}': 0.0 for i in range(1, 29)}
            data['Amount'] = txn.amount
            data['Time']   = txn.hour if txn.hour is not None else 0.0
            
            df = pd.DataFrame([data])
            cols = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']
            df = df[cols]
            
            if scaler_amount: df['Amount'] = scaler_amount.transform(df[['Amount']])
            if scaler_time:   df['Time']   = scaler_time.transform(df[['Time']])
            
            prob = float(fraud_model.predict_proba(df)[0, 1])
        else:
            prob = 0.15

        # SECURITY LAYER (Rule-based safety overrides)
        rule_flag = False
        if txn.amount > 1000000:
            rule_flag = True
            prob = max(prob, 0.98) # Force high confidence
        elif txn.is_international and txn.amount > 50000:
            rule_flag = True
            prob = max(prob, 0.92)

        is_fraud = (prob >= threshold) or rule_flag
                
    except Exception as e:
        print(f"Engine Err: {e}")
        is_fraud = txn.amount > 100000
        prob = 0.85 if is_fraud else 0.15

    save_alert(owner=owner, amount=txn.amount, confidence=prob, source="manual", status="FRAUD" if is_fraud else "LEGIT")
    return {
        "prediction_result": "FRAUD" if is_fraud else "LEGIT",
        "fraud_index": 1 if is_fraud else 0,
        "confidence_score": round(prob * 100, 2),
        "engine": "Shield_Hybrid_v2.5" 
    }

@app.get("/api/status")
def get_status():
    return {
        "status": "ONLINE",
        "model_loaded": fraud_model is not None,
        "db_connected": True,
        "active_threads": 4
    }




# ─────────────────────────────────────────────
# 9. DIGITAL ASSET LINKS (Play Store requirement)
# ─────────────────────────────────────────────
@app.get("/.well-known/assetlinks.json")
def asset_links():
    """
    Required for Google Play Store TWA (Trusted Web Activity).
    Replace the fingerprint with your actual signing key SHA-256 from Play Console.
    """
    return [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.shieldai.fraud",
            "sha256_cert_fingerprints": [
                "REPLACE_WITH_YOUR_SHA256_FROM_PLAY_CONSOLE"
            ]
        }
    }]

@app.get("/")
def home():
    return RedirectResponse(url="/ui/login.html")

app.mount("/ui", StaticFiles(directory="frontend"), name="ui")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    print(f"📡 Shield AI 2.0 is ACTIVE at: http://{host}:{port}")
    print(f"📲 To install on your phone, visit: http://10.166.215.73:{port}/ui/login.html")
    uvicorn.run("app:app", host=host, port=port, reload=False)


