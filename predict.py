import joblib
import pandas as pd
import os

# Configuration
MODEL_PATH = "fraud_model.joblib"
SCALER_AMOUNT_PATH = "scaler_amount.joblib"
SCALER_TIME_PATH = "scaler_time.joblib"

def predict_transaction(data_dict):
    """
    Predicts if a single transaction is fraudulent.
    """
    # Check if files exist
    files = [MODEL_PATH, SCALER_AMOUNT_PATH, SCALER_TIME_PATH]
    if not all(os.path.exists(f) for f in files):
        print(f"[!] Error: Model or Scalers not found. Run 'python fraud_detection.py' first.")
        return

    # Load resources
    model = joblib.load(MODEL_PATH)
    scaler_amount = joblib.load(SCALER_AMOUNT_PATH)
    scaler_time = joblib.load(SCALER_TIME_PATH)

    # Convert to DataFrame
    df = pd.DataFrame([data_dict])

    # Scale the 'Time' and 'Amount' correctly
    df['Amount'] = scaler_amount.transform(df[['Amount']])
    df['Time']   = scaler_time.transform(df[['Time']])

    # Predict
    pred = model.predict(df)[0]
    prob = model.predict_proba(df)[0, 1]

    print("\n" + "="*40)
    print("TRANSACTION PREDICTION RESULT")
    print("="*40)
    if pred == 1:
        print("Outcome: 🔴 FRAUD DETECTED")
        print("Action:  Block transaction and alert user.")
    else:
        print("Outcome: 🟢 LEGIT TRANSACTION")
        print("Action:  Process normally.")
    
    print(f"Confidence: {prob*100:.2f}% (Fraud Probability)")
    print("="*40)

if __name__ == "__main__":
    print("Credit Card Fraud Prediction Utility")
    
    # Example Case from dataset
    # This data is roughly modeled after a known fraud entry
    example_data = {
        "Time": 406.0, "V1": -2.312, "V2": 1.951, "V3": -1.609, "V4": 3.997,
        "V5": -0.522, "V6": -1.426, "V7": -2.537, "V8": 1.391, "V9": -2.770,
        "V10": -2.772, "V11": 3.202, "V12": -2.899, "V13": -0.595, "V14": -4.289,
        "V15": 0.389, "V16": -1.140, "V17": -2.830, "V18": -0.016, "V19": 0.416,
        "V20": 0.126, "V21": 0.517, "V22": -0.035, "V23": -0.465, "V24": 0.320,
        "V25": 0.044, "V26": 0.177, "V27": 0.261, "V28": -0.143, "Amount": 239.93
    }
    
    predict_transaction(example_data)
