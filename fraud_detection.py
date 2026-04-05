# ============================================================
#   Credit Card Fraud Detection — XGBoost + SMOTE
#   Author: Deep Shekhar Halder
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, precision_recall_curve, auc
)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import warnings
import joblib
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
def load_data():
    DATA_PATH = "data/creditcard.csv"
    if not os.path.exists(DATA_PATH):
        print(f"[!] Error: {DATA_PATH} not found.")
        print("Please download 'creditcard.csv' from Kaggle and place it in the 'data' folder.")
        return None
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"Shape: {df.shape}")
    print(f"\nClass distribution:\n{df['Class'].value_counts()}")
    print(f"Fraud %: {df['Class'].mean()*100:.3f}%")
    return df


# ─────────────────────────────────────────────
# 2. EXPLORATORY DATA ANALYSIS (EDA)
# ─────────────────────────────────────────────
def run_eda(df):
    # Plot class imbalance (Optimized for large data)
    counts = df['Class'].value_counts()
    plt.figure(figsize=(6, 4))
    plt.bar(['Legit', 'Fraud'], counts.values, color=['steelblue', 'crimson'])
    plt.title("Class Distribution (0=Legit, 1=Fraud)")
    plt.xticks([0, 1], ['Legit', 'Fraud'])
    plt.savefig("class_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Transaction amount by class
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    df[df['Class'] == 0]['Amount'].hist(bins=50, color='steelblue', alpha=0.7)
    plt.title("Legit Transaction Amounts")
    plt.xlabel("Amount")

    plt.subplot(1, 2, 2)
    df[df['Class'] == 1]['Amount'].hist(bins=50, color='crimson', alpha=0.7)
    plt.title("Fraud Transaction Amounts")
    plt.xlabel("Amount")
    plt.tight_layout()
    plt.savefig("amount_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()


# ─────────────────────────────────────────────
# 3. PREPROCESSING
# ─────────────────────────────────────────────
def preprocess_data(df):
    # Scale 'Amount' and 'Time' using separate scalers (V1-V28 are already PCA-scaled)
    scaler_amount = StandardScaler()
    scaler_time   = StandardScaler()
    df['Amount'] = scaler_amount.fit_transform(df[['Amount']])
    df['Time']   = scaler_time.fit_transform(df[['Time']])

    # Split features and target
    X = df.drop('Class', axis=1)
    y = df['Class']

    # Train-test split (stratified to preserve fraud ratio)
    return train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    ), scaler_amount, scaler_time


# ─────────────────────────────────────────────
# 4. TRAINING & EVALUATION
# ─────────────────────────────────────────────
def train_and_eval(X_train, X_test, y_train, y_test, scaler_amount, scaler_time):
    print("\nApplying SMOTE to balance training data...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"After SMOTE — Legit: {sum(y_train_res==0)}, Fraud: {sum(y_train_res==1)}")

    print("\nTraining XGBoost model...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train_res, y_train_res)
    print("Training complete!")

    y_pred      = model.predict(X_test)
    y_pred_prob = model.predict_proba(X_test)[:, 1]

    print("\n" + "="*50)
    print("CLASSIFICATION REPORT")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))

    roc_auc = roc_auc_score(y_test, y_pred_prob)
    print(f"ROC-AUC Score: {roc_auc:.4f}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Legit', 'Fraud'],
                yticklabels=['Legit', 'Fraud'])
    plt.title(f"Confusion Matrix\nROC-AUC: {roc_auc:.4f}")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.savefig("confusion_matrix.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_pred_prob)
    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC Curve (AUC = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve — Fraud Detection")
    plt.legend(loc="lower right")
    plt.savefig("roc_curve.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, y_pred_prob)
    pr_auc = auc(recall, precision)
    plt.figure(figsize=(7, 5))
    plt.plot(recall, precision, color='green', lw=2, label=f'PR Curve (AUC = {pr_auc:.4f})')
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.savefig("pr_curve.png", dpi=150, bbox_inches='tight')
    plt.close()

    plt.savefig("feature_importance.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ─────────────────────────────────────────────
    # 8. SAVE MODEL AND SCALER
    # ─────────────────────────────────────────────
    print("\nSaving model and scalers...")
    joblib.dump(model, "fraud_model.joblib")
    joblib.dump(scaler_amount, "scaler_amount.joblib")
    joblib.dump(scaler_time, "scaler_time.joblib")
    print("Files saved: 'fraud_model.joblib', 'scaler_amount.joblib', 'scaler_time.joblib'")

    # Export results text
    with open("results.txt", "w") as f:
        f.write("CREDIT CARD FRAUD DETECTION — PERFORMANCE REPORT\n")
        f.write("="*50 + "\n")
        f.write(f"ROC-AUC Score: {roc_auc:.4f}\n")
        f.write("\nCLASSIFICATION REPORT:\n")
        f.write(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))
    print("Metrics exported to 'results.txt'")

def main():
    df = load_data()
    if df is not None:
        run_eda(df)
        (X_train, X_test, y_train, y_test), s_amount, s_time = preprocess_data(df)
        train_and_eval(X_train, X_test, y_train, y_test, s_amount, s_time)
        print("\nAll plots saved. Project complete!")

if __name__ == "__main__":
    main()