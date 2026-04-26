#!/usr/bin/env python3
"""
Firebase Batch Upload Script.

Uploads analysis results from nu-reports/*.json to Firebase Firestore.

Setup:
    1. Create a Firebase project at https://console.firebase.google.com
    2. Go to Project Settings → Service Accounts → Generate New Private Key
    3. Save as firebase-credentials.json in this directory
    4. Run: python firebase_upload.py

Usage:
    python firebase_upload.py                    # Upload all JSON files
    python firebase_upload.py --file NVDA       # Upload specific symbol
    python firebase_upload.py --batch           # Upload BATCH_firebase.json only
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from logging_config import get_logger

logger = get_logger()

# Firebase initialization
_db = None


def init_firebase():
    """Initialize Firebase connection."""
    global _db

    if _db is not None:
        return _db

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        print("ERROR: firebase-admin not installed.")
        print("Run: pip install firebase-admin")
        sys.exit(1)

    # Check for credentials file
    cred_paths = [
        "firebase-credentials.json",
        os.environ.get("FIREBASE_CREDENTIALS", ""),
        "serviceAccountKey.json",
    ]

    cred_path = None
    for path in cred_paths:
        if path and os.path.exists(path):
            cred_path = path
            break

    if not cred_path:
        print("="*60)
        print("FIREBASE CREDENTIALS NOT FOUND")
        print("="*60)
        print()
        print("To set up Firebase:")
        print()
        print("1. Go to https://console.firebase.google.com")
        print("2. Create a new project (or select existing)")
        print("3. Click the gear icon → Project Settings")
        print("4. Go to 'Service Accounts' tab")
        print("5. Click 'Generate New Private Key'")
        print("6. Save the file as 'firebase-credentials.json' in:")
        print(f"   {os.getcwd()}")
        print()
        print("Or set the FIREBASE_CREDENTIALS environment variable:")
        print("   export FIREBASE_CREDENTIALS=/path/to/credentials.json")
        print("="*60)
        sys.exit(1)

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        print(f"✓ Firebase initialized with: {cred_path}")
        return _db
    except Exception as e:
        print(f"ERROR: Failed to initialize Firebase: {e}")
        sys.exit(1)


def upload_analysis(db, data: dict, symbol: str) -> str:
    """
    Upload a single analysis to Firestore.

    Creates documents in:
    - analyses/{id}
    - signals/{id} (multiple)
    - ai_outputs/{id}

    Returns the analysis document ID.
    """
    from google.cloud.firestore import SERVER_TIMESTAMP

    # Extract components
    analysis_data = data.get("analysis", data)
    signals_data = data.get("signals", [])
    ai_data = data.get("ai_analysis", None)

    # Create analysis document
    analysis_doc = {
        "symbol": symbol,
        "interval": analysis_data.get("interval", "1d"),
        "timestamp": SERVER_TIMESTAMP,
        "imported_at": datetime.utcnow().isoformat(),
        "bars_analyzed": analysis_data.get("bars_analyzed", 0),
        "indicators": analysis_data.get("indicators", {}),
        "signal_summary": analysis_data.get("signal_summary", {}),
        "ai_enabled": ai_data is not None,
    }

    # Upload analysis
    analysis_ref = db.collection("analyses").document()
    analysis_ref.set(analysis_doc)
    analysis_id = analysis_ref.id

    # Upload signals
    signals_uploaded = 0
    if signals_data:
        batch = db.batch()
        for signal in signals_data:
            signal_doc = {
                "analysis_id": analysis_id,
                "symbol": symbol,
                "timestamp": SERVER_TIMESTAMP,
                "name": signal.get("name"),
                "category": signal.get("category"),
                "strength": signal.get("strength"),
                "confidence": signal.get("confidence"),
                "description": signal.get("description"),
                "trading_implication": signal.get("trading_implication"),
                "value": signal.get("value"),
                "indicator_name": signal.get("indicator_name"),
            }
            signal_ref = db.collection("signals").document()
            batch.set(signal_ref, signal_doc)
            signals_uploaded += 1
        batch.commit()

    # Upload AI output
    if ai_data:
        ai_doc = {
            "timestamp": SERVER_TIMESTAMP,
            "signal_summary": ai_data.get("signal_summary"),
            "trading_recommendation": ai_data.get("trading_recommendation"),
            "risk_assessment": ai_data.get("risk_assessment"),
            "volatility_regime": ai_data.get("volatility_regime"),
            "opportunities": ai_data.get("opportunities", []),
            "alerts": ai_data.get("alerts", []),
        }
        db.collection("ai_outputs").document(analysis_id).set(ai_doc)

    return analysis_id, signals_uploaded


def upload_file(db, filepath: str) -> dict:
    """Upload a single JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Extract symbol from filename or data
    filename = os.path.basename(filepath)
    symbol = filename.replace("_firebase.json", "").upper()

    if symbol == "BATCH":
        # Handle batch file
        results = {}
        analyses = data.get("analyses", {})
        for sym, sym_data in analyses.items():
            try:
                analysis_id, signals = upload_analysis(db, sym_data, sym)
                results[sym] = {"id": analysis_id, "signals": signals, "success": True}
                print(f"  ✓ {sym}: {analysis_id} ({signals} signals)")
            except Exception as e:
                results[sym] = {"error": str(e), "success": False}
                print(f"  ✗ {sym}: {e}")
        return results
    else:
        # Single file
        analysis_id, signals = upload_analysis(db, data, symbol)
        return {symbol: {"id": analysis_id, "signals": signals, "success": True}}


def main():
    parser = argparse.ArgumentParser(description="Upload analysis to Firebase")
    parser.add_argument("--file", "-f", help="Specific symbol to upload (e.g., NVDA)")
    parser.add_argument("--batch", "-b", action="store_true", help="Upload BATCH_firebase.json only")
    parser.add_argument("--all", "-a", action="store_true", help="Upload all individual files")
    parser.add_argument("--dir", "-d", default="nu-reports", help="Directory containing JSON files")
    args = parser.parse_args()

    # Initialize Firebase
    db = init_firebase()

    reports_dir = Path(args.dir)
    if not reports_dir.exists():
        print(f"ERROR: Directory not found: {reports_dir}")
        sys.exit(1)

    results = {}

    if args.file:
        # Upload specific file
        filepath = reports_dir / f"{args.file.upper()}_firebase.json"
        if not filepath.exists():
            print(f"ERROR: File not found: {filepath}")
            sys.exit(1)
        print(f"Uploading {filepath}...")
        results = upload_file(db, str(filepath))

    elif args.batch:
        # Upload batch file only
        filepath = reports_dir / "BATCH_firebase.json"
        if not filepath.exists():
            print(f"ERROR: Batch file not found: {filepath}")
            sys.exit(1)
        print(f"Uploading batch file...")
        results = upload_file(db, str(filepath))

    else:
        # Upload all individual files (default)
        json_files = list(reports_dir.glob("*_firebase.json"))
        json_files = [f for f in json_files if "BATCH" not in f.name]

        if not json_files:
            print(f"No JSON files found in {reports_dir}")
            sys.exit(1)

        print(f"Uploading {len(json_files)} files...")
        print("-" * 40)

        for filepath in sorted(json_files):
            try:
                file_results = upload_file(db, str(filepath))
                results.update(file_results)
            except Exception as e:
                symbol = filepath.stem.replace("_firebase", "").upper()
                results[symbol] = {"error": str(e), "success": False}
                print(f"  ✗ {symbol}: {e}")

    # Summary
    print()
    print("=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)

    success = sum(1 for r in results.values() if r.get("success"))
    failed = len(results) - success
    total_signals = sum(r.get("signals", 0) for r in results.values() if r.get("success"))

    print(f"Uploaded: {success} analyses")
    print(f"Failed: {failed}")
    print(f"Total signals: {total_signals}")

    if success > 0:
        print()
        print("Document IDs:")
        for symbol, r in sorted(results.items()):
            if r.get("success"):
                print(f"  {symbol}: {r['id']}")

    print()
    print("View in Firebase Console:")
    print("https://console.firebase.google.com/project/_/firestore")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
