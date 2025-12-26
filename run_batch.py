#!/usr/bin/env python3
"""
Batch analysis runner with Firebase export.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzer import analyze_with_ai, analyze_multiple
from logging_config import get_logger

logger = get_logger()

SYMBOLS = [
    "AAPL", "ABBV", "AMD", "AMGN", "ARQQ", "AVGO", "BABA", "BAC", "BBAI", "BIIB",
    "BIDU", "ETHA", "GILD", "GLD", "GOOG", "GS", "HON", "HOOD", "IBIT", "IBM",
    "IONQ", "JD", "JNJ", "JPM", "LLY", "LRCX", "MA", "MP", "MRNA", "MSFT",
    "NVDA", "ORCL", "PDD", "PFE", "PLTR", "QBTS", "QQQ", "QUBT", "REGN", "RGTI",
    "ROKU", "SMCI", "SPY", "TSLA", "TSM", "UNH", "V", "VRTX", "WFC", "XBI"
]


def result_to_firebase_dict(result) -> dict:
    """Convert EnhancedAnalysisResult to Firebase-compatible dict."""
    base = result.base_result

    # Extract indicators
    indicators = {}
    if hasattr(base, 'indicators') and base.indicators:
        for name, value in base.indicators.items():
            if isinstance(value, (int, float)):
                indicators[name] = value
            elif hasattr(value, 'tolist'):
                indicators[name] = float(value) if value.size == 1 else value.tolist()

    # Build analysis dict
    analysis = {
        "symbol": result.symbol,
        "interval": getattr(base, 'interval', '1d'),
        "bars_analyzed": getattr(base, 'bars_analyzed', 0),
        "indicators": indicators,
        "signal_summary": {
            "total": base.signals.signal_count if hasattr(base, 'signals') else 0,
            "bullish": base.signals.bullish_count if hasattr(base, 'signals') else 0,
            "bearish": base.signals.bearish_count if hasattr(base, 'signals') else 0,
            "neutral": base.signals.neutral_count if hasattr(base, 'signals') else 0,
        }
    }

    # Extract signals
    signals = []
    if hasattr(base, 'signals') and hasattr(base.signals, 'signals'):
        for sig in base.signals.signals:
            signals.append({
                "name": getattr(sig, 'name', ''),
                "category": getattr(sig, 'category', ''),
                "strength": getattr(sig, 'strength', 'NEUTRAL'),
                "confidence": getattr(sig, 'confidence', 0.5),
                "description": getattr(sig, 'description', ''),
                "trading_implication": getattr(sig, 'trading_implication', ''),
                "value": getattr(sig, 'value', None),
                "indicator_name": getattr(sig, 'indicator_name', ''),
            })

    # Extract AI analysis
    ai_analysis = None
    if result.ai_result:
        ai = result.ai_result
        ai_analysis = {
            "signal_summary": getattr(ai, 'signal_summary', {}),
            "trading_recommendation": getattr(ai, 'trading_recommendation', {}),
            "risk_assessment": getattr(ai, 'risk_assessment', {}),
            "volatility_regime": getattr(ai, 'volatility_regime', {}),
            "opportunities": getattr(ai, 'opportunities', []),
            "alerts": getattr(ai, 'alerts', []),
        }

    return {
        "analysis": analysis,
        "signals": signals,
        "ai_analysis": ai_analysis,
    }


def main():
    print("=" * 60)
    print("BATCH ANALYSIS WITH AI")
    print(f"Symbols: {len(SYMBOLS)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    reports_dir = Path("nu-reports")
    reports_dir.mkdir(exist_ok=True)

    results = {}
    failed = []

    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/{len(SYMBOLS)}] Analyzing {symbol}...")
        try:
            result = analyze_with_ai(symbol, interval='1d')
            firebase_data = result_to_firebase_dict(result)
            results[symbol] = firebase_data

            # Write individual file
            filepath = reports_dir / f"{symbol}_firebase.json"
            with open(filepath, 'w') as f:
                json.dump(firebase_data, f, indent=2, default=str)

            signal_count = firebase_data['analysis']['signal_summary']['total']
            has_ai = firebase_data['ai_analysis'] is not None
            print(f"  ✓ {symbol}: {signal_count} signals, AI: {has_ai}")

        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
            failed.append(symbol)

    # Write batch file
    batch_data = {
        "generated_at": datetime.now().isoformat(),
        "symbol_count": len(results),
        "analyses": results,
    }

    batch_path = reports_dir / "BATCH_firebase.json"
    with open(batch_path, 'w') as f:
        json.dump(batch_data, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Success: {len(results)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed symbols: {', '.join(failed)}")
    print(f"\nOutput: {reports_dir}")
    print(f"Batch file: {batch_path}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
