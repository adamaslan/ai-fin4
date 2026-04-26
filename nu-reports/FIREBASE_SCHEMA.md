# Firebase Database Schema

**Version:** 1.0
**Last Updated:** December 25, 2025

---

## Overview

This document describes the Firebase Firestore schema for storing signal analyzer results. The schema is designed to be:

- **Dynamic**: New signals, indicators, and AI outputs can be added without schema changes
- **Queryable**: Optimized for common query patterns
- **JSON-Compatible**: Mirrors the JSON export format for consistency

---

## Collections

### 1. `analyses` (Main Analysis Results)

Stores the primary analysis document for each run.

```javascript
analyses/{analysis_id}
{
    "symbol": "NVDA",                    // Stock symbol
    "interval": "1d",                    // Timeframe
    "timestamp": Timestamp,              // When analysis was run
    "bars_analyzed": 250,                // Number of price bars
    "indicators": {                      // Dynamic indicator map
        "RSI": 56.3,
        "MACD": -0.37,
        "MACD_Signal": -1.72,
        "SMA_10": 179.75,
        "SMA_20": 180.79,
        "SMA_50": 185.84,
        "SMA_100": 182.64,
        "SMA_200": 158.71,
        "ATR": 5.23,
        "ADX": 22.4,
        "OBV": 2460000000,
        "Current_Price": 188.61,
        // ... additional indicators added dynamically
    },
    "signal_summary": {
        "total": 6,
        "bullish": 1,
        "bearish": 1,
        "neutral": 4
    },
    "ai_enabled": true
}
```

**Indexes:**
- `symbol` + `timestamp` (compound, descending)
- `interval` + `timestamp` (compound, descending)
- `ai_enabled` + `timestamp` (compound, descending)

---

### 2. `signals` (Individual Signals)

Stores each detected signal as a separate document for granular querying.

```javascript
signals/{signal_id}
{
    "analysis_id": "abc123",             // Reference to parent analysis
    "symbol": "NVDA",
    "timestamp": Timestamp,
    "name": "PRICE ABOVE ALL MAs",       // Signal identifier
    "category": "MA_POSITION",           // Category for filtering
    "strength": "BULLISH",               // BULLISH, BEARISH, NEUTRAL, etc.
    "confidence": 0.80,                  // 0.0 - 1.0
    "description": "Price is above all moving averages: (20, 50, 200)",
    "trading_implication": "Strong uptrend; favor long positions",
    "value": 188.61,                     // Optional: signal value
    "indicator_name": "SMA",             // Optional: source indicator
    "timeframe": "1d"                    // Optional: timeframe context
}
```

**Indexes:**
- `symbol` + `timestamp` (compound, descending)
- `symbol` + `category` + `timestamp` (compound, descending)
- `category` + `timestamp` (compound, descending)
- `strength` + `timestamp` (compound, descending)
- `analysis_id` (single field)

**Supported Categories:**
| Category | Description |
|----------|-------------|
| `MA_CROSS` | Moving average crossovers |
| `MA_POSITION` | Price position relative to MAs |
| `MA_RIBBON` | MA ribbon alignment |
| `RSI` | RSI overbought/oversold |
| `MACD` | MACD crossovers |
| `STOCHASTIC` | Stochastic oscillator |
| `FIBONACCI` | Fibonacci levels/zones |
| `VOLUME` | Volume-based signals |
| `DIVERGENCE` | Price/indicator divergences |
| `PATTERN` | Chart patterns |

---

### 3. `indicators_history` (Time-Series Tracking)

Tracks indicator values over time for trend analysis.

```javascript
indicators_history/{symbol}/{interval}/{timestamp}
{
    "timestamp": Timestamp,
    "values": {
        "RSI": 56.3,
        "MACD": -0.37,
        "SMA_20": 180.79,
        "ATR": 5.23,
        // ... all indicator values at this point
    }
}
```

**Structure:**
```
indicators_history/
├── NVDA/
│   ├── 1d/
│   │   ├── 2025-12-25T00:00:00/
│   │   ├── 2025-12-24T00:00:00/
│   │   └── ...
│   ├── 1h/
│   │   └── ...
│   └── 5m/
│       └── ...
├── AAPL/
│   └── ...
└── SPY/
    └── ...
```

---

### 4. `ai_outputs` (AI Analysis Results)

Stores AI-generated analysis, linked to main analysis document.

```javascript
ai_outputs/{analysis_id}
{
    "timestamp": Timestamp,
    "signal_summary": "## Trading Signal Synthesis...",  // Full AI interpretation
    "trading_recommendation": {
        "recommendation": "SHORT",       // BUY, SELL, HOLD, SHORT, etc.
        "entry": 188.61,
        "stop_loss": 198.15,
        "target": 169.48,
        "risk_reward_ratio": 1.5,
        "confidence": 0.65,
        "reasoning": "Price is above all MAs but momentum exhausted",
        "position_size_adjustment": "3/4 SIZE - Acceptable risk/reward"
    },
    "risk_assessment": {
        "overall_risk_level": "LOW",     // LOW, MEDIUM, HIGH
        "identified_risks": [
            "Overbought conditions",
            "Potential mean reversion"
        ],
        "mitigations": [
            "Use tight stop loss",
            "Scale into position"
        ]
    },
    "volatility_regime": {
        "regime": "LOW_VOLATILITY",      // LOW, MEDIUM, HIGH, EXTREME
        "hv": 0.25,                       // Historical volatility
        "atr_pct": 2.8,                   // ATR as % of price
        "recommended_strategy": "Trend following with tight stops"
    },
    "opportunities": [
        {
            "type": "SIGNAL_CONVERGENCE",
            "description": "4 weak signals converging - watch for breakout",
            "entry_trigger": "Price breaks above/below recent range",
            "action": "WATCH - Not ready to trade yet",
            "confidence": 0.6
        }
    ],
    "alerts": [
        "RSI approaching overbought",
        "Volume declining on rally"
    ]
}
```

---

## Query Patterns

### Get Latest Analysis for Symbol

```python
db.collection('analyses')
  .where('symbol', '==', 'NVDA')
  .order_by('timestamp', direction='DESCENDING')
  .limit(1)
```

### Get All Bullish Signals This Week

```python
from datetime import datetime, timedelta
week_ago = datetime.now() - timedelta(days=7)

db.collection('signals')
  .where('strength', '==', 'BULLISH')
  .where('timestamp', '>=', week_ago)
  .order_by('timestamp', direction='DESCENDING')
```

### Get RSI History for Symbol

```python
db.collection('indicators_history')
  .document('NVDA')
  .collection('1d')
  .order_by('timestamp', direction='DESCENDING')
  .limit(30)
```

### Get Recent AI Recommendations

```python
db.collection('analyses')
  .where('ai_enabled', '==', True)
  .order_by('timestamp', direction='DESCENDING')
  .limit(10)
```

---

## Adding New Data Types

### Adding a New Indicator

No schema changes required. Simply add to the `indicators` map:

```python
# In indicator calculation code
indicators["NEW_INDICATOR"] = calculated_value

# Stored automatically in:
# - analyses/{id}/indicators/NEW_INDICATOR
# - indicators_history/{symbol}/{interval}/{ts}/values/NEW_INDICATOR
```

### Adding a New Signal Category

No schema changes required. Use a new category string:

```python
Signal(
    name="NEW_PATTERN_DETECTED",
    category="NEW_CATEGORY",  # Just use a new category string
    strength="BULLISH",
    ...
)
```

### Adding New AI Output Fields

Add to the `ai_outputs` document dynamically:

```python
ai_doc["new_ai_field"] = {
    "analysis": "...",
    "confidence": 0.8
}
```

---

## Security Rules (Recommended)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Analyses: read-only for authenticated users
    match /analyses/{analysisId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
                      request.auth.token.admin == true;
    }

    // Signals: read-only for authenticated users
    match /signals/{signalId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
                      request.auth.token.admin == true;
    }

    // Indicators history: read-only
    match /indicators_history/{symbol}/{interval}/{timestamp} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
                      request.auth.token.admin == true;
    }

    // AI outputs: read-only for authenticated users
    match /ai_outputs/{analysisId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
                      request.auth.token.admin == true;
    }
  }
}
```

---

## JSON Export Format

The `export_to_firebase_json()` function creates JSON that mirrors this schema:

```json
{
  "analysis": {
    "symbol": "NVDA",
    "interval": "1d",
    "timestamp": "2025-12-25T01:18:20.000Z",
    "bars_analyzed": 250,
    "indicators": {
      "RSI": 56.3,
      "MACD": -0.37,
      "SMA_20": 180.79
    },
    "signal_summary": {
      "total": 6,
      "bullish": 1,
      "bearish": 1,
      "neutral": 4
    }
  },
  "signals": [
    {
      "name": "PRICE ABOVE ALL MAs",
      "category": "MA_POSITION",
      "strength": "BULLISH",
      "confidence": 0.8,
      "description": "Price is above all moving averages"
    }
  ],
  "ai_analysis": {
    "signal_summary": "## Trading Signal Synthesis...",
    "trading_recommendation": {
      "recommendation": "SHORT",
      "entry": 188.61,
      "target": 169.48
    }
  }
}
```

---

## Setup Instructions

### 1. Create Firebase Project

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize project
firebase init firestore
```

### 2. Download Service Account Key

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `firebase-credentials.json` in project root

### 3. Configure Environment

```bash
# .env file
FIREBASE_CREDENTIALS=firebase-credentials.json
```

### 4. Install SDK

```bash
pip install firebase-admin
```

### 5. Test Connection

```python
from firebase_db import get_firebase_db

db = get_firebase_db()
if db.is_connected:
    print("Firebase connected!")
```

---

## Usage Examples

### Store Analysis Result

```python
from analyzer import analyze_with_ai
from firebase_db import store_analysis

result = analyze_with_ai('NVDA', interval='1d')
analysis_id = store_analysis(result)
print(f"Stored: {analysis_id}")
```

### Export to JSON

```python
from analyzer import analyze_with_ai
from firebase_db import export_to_firebase_json

result = analyze_with_ai('NVDA', interval='1d')
export_to_firebase_json(result, 'nu-reports/NVDA_analysis.json')
```

### Query History

```python
from firebase_db import get_firebase_db

db = get_firebase_db()

# Get last 10 analyses
history = db.get_analysis_history('NVDA', limit=10)

# Get RSI signals
rsi_signals = db.get_signals_by_category('NVDA', 'RSI', limit=50)

# Get indicator trend
rsi_history = db.get_indicator_history('NVDA', indicator='RSI', limit=30)
```

---

*This schema is designed to be production-ready and scalable for real-time trading applications.*
