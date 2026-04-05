import os
import subprocess
import sys

REQUIRED_PACKAGES = [
    "razorpay",
    "python-dotenv",
    "aiofiles",
    "python-multipart",
]

def install_missing():
    """Auto-install any missing packages before starting."""
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"[~] Installing missing package: {pkg}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                check=True
            )
            print(f"[+] {pkg} installed.")

def check_models():
    files = ["fraud_model.joblib", "scaler_amount.joblib", "scaler_time.joblib"]
    return all(os.path.exists(f) for f in files)

def main():
    print("=" * 55)
    print("  SHIELD AI v2.0 — FRAUD DETECTION SYSTEM")
    print("=" * 55)

    # Auto-install missing packages
    print("\n[~] Checking dependencies...")
    install_missing()
    print("[+] All dependencies ready.\n")

    if not check_models():
        print("[!] Model files not found. Starting training pipeline...")
        try:
            subprocess.run([sys.executable, "fraud_detection.py"], check=True)
            print("[+] Training complete.")
        except subprocess.CalledProcessError:
            print("[X] Training failed. Check fraud_detection.py.")
            return
    else:
        print("[+] Models detected. Skipping training.")

    if not os.path.exists("shield_ai.db"):
        print("[!] Database will be initialized on startup.")

    print("\n[+] Starting Shield AI v2.0 at http://127.0.0.1:8000")
    print("[+] Razorpay status:  http://127.0.0.1:8000/razorpay/status")
    print("[+] API Docs:         http://127.0.0.1:8000/docs\n")

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", host,
            "--port", str(port),
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n[!] Shield AI stopped. Stay safe.")
    except subprocess.CalledProcessError as e:
        print(f"\n[X] Server failed to start: {e}")
        print("    → Check app.py for syntax errors")
        print("    → Run: .venv\\Scripts\\python.exe app.py")
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")

if __name__ == "__main__":
    main()
