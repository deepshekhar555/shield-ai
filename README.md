# 🛡️ Shield AI — Real-Time Credit Card Fraud Detection

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange?style=flat)](https://xgboost.ai)
[![Razorpay](https://img.shields.io/badge/Razorpay-Integrated-0D3C9E?style=flat)](https://razorpay.com)
[![PWA](https://img.shields.io/badge/PWA-Play Store Ready-5A0FC8?style=flat)](https://web.dev/progressive-web-apps/)

A production-grade AI-powered credit card fraud detection system with a mobile-first UI, real Razorpay payment gateway integration, and XGBoost machine learning backend.

---

## ✨ Features

- 🤖 **XGBoost AI Model** — Trained on 284,807 real bank transactions (99.1% accuracy)
- 💳 **AI Risk Scorer** — Multi-factor analysis: Amount + Time + Card Type
- 🔔 **Razorpay Webhooks** — Real-time fraud detection on live payment events
- 👤 **Per-User Isolation** — Each user sees only their own fraud activity
- 🌐 **Merchant Sentinel** — URL phishing & trust verification
- 📱 **PWA Ready** — Installable as Android app via Play Store (TWA/Bubblewrap)
- 🌙 **Dark/Light Mode** — System-aware theme switching
- 📊 **Risk Telemetry** — Live chart of transaction risk probabilities
- 📥 **Export Audit Trail** — Download fraud history as CSV

---

## 🚀 Live Demo

> Deploy your own instance — see setup below

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| ML Model | XGBoost (scikit-learn pipeline) |
| Database | SQLite (auto-migrating schema) |
| Frontend | Vanilla JS + CSS + Lucide Icons |
| Payments | Razorpay Webhooks |
| Deployment | Railway.app |

---

## ⚙️ Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/shield-ai.git
cd shield-ai

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
# → Edit .env with your Razorpay keys

# 5. Start the server
python run.py
```

Open `http://127.0.0.1:8000` — login with `deephalder` / `shield123`

---

## 🔑 Environment Variables

Create a `.env` file from `.env.example`:

```env
RAZORPAY_KEY_ID=rzp_test_your_key_here
RAZORPAY_KEY_SECRET=your_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

Get your test keys from [Razorpay Dashboard](https://dashboard.razorpay.com) → Settings → API Keys

---

## 🌐 Deploy to Railway (Free)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select this repo → Railway auto-detects `railway.json`
4. Add environment variables in Railway → Variables tab
5. Your app goes live at `https://your-app.up.railway.app` 🚀

---

## 📱 Publish to Play Store

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest=https://your-app.up.railway.app/ui/manifest.json
bubblewrap build
# Upload the .aab file to Google Play Console ($25 one-time fee)
```

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/predict` | XGBoost fraud prediction |
| `POST` | `/razorpay/webhook` | Live payment fraud detection |
| `GET` | `/api/alerts` | User's fraud alert history |
| `DELETE` | `/api/alerts` | Clear user's alert history |
| `POST` | `/api/login` | User authentication |
| `POST` | `/api/register` | New user registration |
| `GET` | `/api/alerts/export` | Download audit CSV |
| `GET` | `/razorpay/status` | Integration status check |
| `GET` | `/docs` | Interactive API docs (Swagger) |

---

## 👨‍💻 Author

**Deep Shekhar Halder** — Shield AI v2.0

---

## 📄 License

MIT License — Free to use, modify, and distribute.
