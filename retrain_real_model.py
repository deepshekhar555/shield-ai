"""
Shield AI — Real Gateway Model Trainer
=======================================
This script retrains the fraud model using features that
a real payment gateway (Razorpay/Stripe) actually provides.

Instead of V1-V28 (bank-internal PCA features), we use:
  - Amount (transaction value)
  - Hour (hour of day)
  - IsInternational (card from outside India)
  - IsCard (card vs UPI/netbanking)
  - IsNight (transaction between 10PM–6AM)
  - IsFailed (failed payment attempt)
  - NoIssuerInfo (anonymous card — high risk)

Run this script ONCE to generate real_fraud_model.joblib
Then Razorpay webhooks will use it automatically.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import os

print("=" * 60)
print("  Shield AI — Real Gateway Model Trainer")
print("=" * 60)

# ── STEP 1: Load Kaggle Dataset ──────────────────────────────
CSV_PATH = os.path.join("data", "creditcard.csv")
if not os.path.exists(CSV_PATH):
    # Try root directory
    CSV_PATH = "creditcard.csv"

if not os.path.exists(CSV_PATH):
    print("\n[!] creditcard.csv not found!")
    print("    Download from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
    print("    Place it in the 'data/' folder and re-run this script.")
    exit(1)

print(f"\n[1] Loading dataset from: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)
print(f"    Rows: {len(df):,} | Frauds: {df['Class'].sum():,} ({df['Class'].mean()*100:.2f}%)")

# ── STEP 2: Engineer Real Gateway Features ───────────────────
print("\n[2] Engineering real payment gateway features...")

df["Hour"]          = (df["Time"] % 86400) / 3600          # Hour of day (0-23)
df["IsNight"]       = df["Hour"].apply(lambda h: 1 if h < 6 or h > 22 else 0)
df["IsHighAmount"]  = (df["Amount"] > 500).astype(int)      # High value
df["IsLowAmount"]   = (df["Amount"] < 5).astype(int)        # Micro transaction (suspicious)
df["IsFailed"]      = 0                                      # 0 = captured (kaggle only has success)
df["IsCard"]        = 1                                      # All kaggle records are card
df["IsInternational"] = 0                                    # Unknown — treated as domestic
df["NoIssuerInfo"]  = 0                                      # Unknown

# Selected features that map to real gateway data
FEATURES = ["Amount", "Hour", "IsNight", "IsHighAmount", "IsLowAmount",
            "IsFailed", "IsCard", "IsInternational", "NoIssuerInfo"]

X = df[FEATURES]
y = df["Class"]

print(f"    Features: {FEATURES}")

# ── STEP 3: Balance Dataset ──────────────────────────────────
print("\n[3] Balancing dataset (fraud is rare — 0.17%)...")
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)
print(f"    After SMOTE: {len(X_balanced):,} samples | Fraud ratio: {y_balanced.mean()*100:.1f}%")

# ── STEP 4: Train/Test Split ─────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
)

# ── STEP 5: Scale Features ───────────────────────────────────
print("\n[4] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ── STEP 6: Train Model ──────────────────────────────────────
print("\n[5] Training RandomForest model...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

# ── STEP 7: Evaluate ─────────────────────────────────────────
print("\n[6] Evaluating model...")
y_pred  = model.predict(X_test_scaled)
y_proba = model.predict_proba(X_test_scaled)[:, 1]

print("\n" + classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

# ── STEP 8: Save Model ───────────────────────────────────────
print("\n[7] Saving model files...")
joblib.dump(model,  "real_fraud_model.joblib")
joblib.dump(scaler, "real_scaler.joblib")
joblib.dump(FEATURES, "real_features.joblib")

print("\n✅ Done! Files saved:")
print("   - real_fraud_model.joblib")
print("   - real_scaler.joblib")
print("   - real_features.joblib")
print("\n🚀 Restart app.py — Razorpay webhooks will now use the real model!")
print("=" * 60)
