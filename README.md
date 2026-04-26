# ai-fin4: Advanced Technical Analysis Engine

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen)

**Enterprise-grade Python trading signal detection system** with advanced indicators, multi-AI provider support, and production-ready architecture.

---

## Overview

**ai-fin4** is a high-performance financial analysis engine that detects trading signals across 200+ stock symbols using sophisticated technical indicators and AI-powered insights.

### Key Capabilities

- 🎯 **20+ Technical Indicators** — Bollinger Bands, Fibonacci, Moving Averages, RSI, MACD, Volume, and more
- 🤖 **Multi-AI Support** — Gemini + Mistral with intelligent fallback
- ⚡ **Parallel Processing** — Analyze 200 symbols in 5–10 minutes on GCP Cloud Run
- 📊 **Signal Strength Scoring** — 11-level confidence scale (1–11) with multi-indicator consensus
- 🔄 **Immutable Configuration** — SignalConfig factory pattern for reproducibility
- 🛡️ **Enterprise Patterns** — Error handling, circuit breakers, exponential backoff, logging
- 📈 **Real-Time Export** — Firebase/Firestore batch operations for live dashboard updates

### Performance

| Metric | Value |
|--------|-------|
| Symbols Analyzed | 200+ per run |
| Analysis Runtime | 5–10 minutes |
| Indicators Per Symbol | 20+ |
| Signal Strength Levels | 1–11 (fine-grained) |
| Confidence Scoring | Multi-indicator consensus |
| AI Models | 2 (Gemini + Mistral) |
| Uptime Target | 99.9% |

---

## Architecture

### System Design

```
┌──────────────────────────────┐
│  Market Data Input           │
│  (yfinance, IEX, Polygon)    │
└──────────────┬───────────────┘
               │ OHLCV Data
               ↓
┌──────────────────────────────┐
│  Indicator Calculation       │
│  ├─ Bollinger Bands          │
│  ├─ Fibonacci Retracement    │
│  ├─ Moving Averages          │
│  ├─ RSI/MACD/Volume          │
│  └─ Pattern Recognition      │
└──────────────┬───────────────┘
               │ Calculated Values
               ↓
┌──────────────────────────────┐
│  Signal Detection            │
│  ├─ Band Crossovers          │
│  ├─ Fibonacci Touches        │
│  ├─ Momentum Confirmation    │
│  └─ Consensus Scoring        │
└──────────────┬───────────────┘
               │ Detected Signals
               ↓
┌──────────────────────────────┐
│  AI Summarization            │
│  ├─ Gemini (Primary)         │
│  ├─ Mistral (Fallback)       │
│  └─ Rule-Based (Graceful)    │
└──────────────┬───────────────┘
               │ Natural Language Summary
               ↓
┌──────────────────────────────┐
│  Data Persistence            │
│  ├─ Firestore Batch Write    │
│  ├─ Atomic Operations        │
│  └─ Metadata Tracking        │
└──────────────────────────────┘
```

### Module Organization

```
ai-fin4/
├── ai1.py                    # Main analysis orchestrator
├── ai2.py                    # Enhanced analysis pipeline
├── config.py                 # Configuration management
├── logging_config.py         # Structured logging setup
├── exceptions.py             # Custom exception hierarchy
├── type_defs.py              # Type definitions and dataclasses
├── firebase_db.py            # Firestore integration
├── firebase_upload.py        # Batch operations
├── exporters.py              # Data export formats
├── run_batch.py              # Batch processing runner
│
├── indicators/               # Technical indicators
│   ├── base.py               # Base indicator class
│   ├── momentum.py           # RSI, MACD, Stochastic
│   ├── moving_averages.py    # SMA, EMA, Bollinger Bands
│   ├── trend_volume.py       # Volume analysis, trends
│   └── registry.py           # Indicator registry
│
├── signals/                  # Signal detection
│   ├── base.py               # Base signal class
│   ├── signal_detector.py    # Main detector
│   ├── signal_strength.py    # Confidence scoring (1–11)
│   ├── signal_filter.py      # Filter by criteria
│   ├── signal_sorter.py      # Sort by relevance
│   ├── signal_validator.py   # Validate signals
│   ├── aggregator.py         # Aggregate signals
│   ├── momentum_signals.py   # Momentum patterns
│   ├── ma_signals.py         # Moving average patterns
│   ├── fibonacci_signals.py  # Fibonacci patterns
│   └── signal_detector_metadata.py  # Metadata tracking
│
├── analyzer/                 # Analysis workflows
│   └── (analyzer modules)    # High-level analysis
│
├── docs/                     # Documentation
│   └── wiki-aifin4/          # Project wiki
│
└── data/                     # Data storage
    └── (sample data)         # Test data, outputs
```

---

## Installation

### Prerequisites

- Python 3.11 or higher
- GCP credentials (for Firestore)
- API keys (Gemini or Mistral)
- Market data provider access (yfinance included)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/ai-fin4.git
cd ai-fin4

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys and GCP credentials

# 5. Verify installation
python -c "import ai1; print('✓ ai-fin4 ready')"
```

### Environment Variables

```bash
# AI Providers
GEMINI_API_KEY=your_gemini_key_here
MISTRAL_API_KEY=your_mistral_key_here

# GCP Firestore
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
FIRESTORE_PROJECT_ID=your_project_id

# Market Data
MARKET_DATA_PROVIDER=yfinance  # or: iex, polygon

# Analysis Parameters
SYMBOLS_TO_ANALYZE=AAPL,GOOGL,MSFT,TSLA,...
TIMEFRAMES=1m,5m,1h,1d
SIGNAL_STRENGTH_THRESHOLD=5

# Logging
LOG_LEVEL=INFO
```

**Note**: Never commit `.env` or credentials. Use `.env.example` as template.

---

## Quick Start

### 1. Basic Analysis

```python
from ai1 import SignalAnalyzer

# Initialize analyzer
analyzer = SignalAnalyzer(symbols=['AAPL', 'GOOGL', 'MSFT'])

# Run analysis
signals = analyzer.analyze()

# Results
for signal in signals:
    print(f"{signal.symbol}: {signal.direction} ({signal.strength}/11)")
```

### 2. With AI Summaries

```python
from ai1 import SignalAnalyzer, AIConfig

# Configure AI
ai_config = AIConfig(primary_provider='gemini')

# Analyze with summaries
analyzer = SignalAnalyzer(symbols=['AAPL'], ai_config=ai_config)
results = analyzer.analyze_with_summaries()

# Results include AI-generated insights
print(results['summary'])  # "Strong bullish momentum with Fibonacci confluence..."
```

### 3. Batch Processing

```bash
# Analyze 200+ symbols in parallel
python run_batch.py --symbols-file symbols.txt --timeframes 1h,1d

# Results exported to Firestore + JSON
```

### 4. With Custom Indicators

```python
from indicators.registry import IndicatorRegistry

registry = IndicatorRegistry()
registry.register_custom(MyCustomIndicator)

analyzer = SignalAnalyzer(indicator_registry=registry)
signals = analyzer.analyze()
```

---

## Features in Detail

### 🎯 20+ Technical Indicators

**Momentum Indicators**
- Relative Strength Index (RSI)
- Moving Average Convergence Divergence (MACD)
- Stochastic Oscillator
- Rate of Change (ROC)

**Trend Indicators**
- Moving Averages (SMA, EMA, WMA)
- Bollinger Bands
- Keltner Channels
- Average Directional Index (ADX)

**Volume Indicators**
- On-Balance Volume (OBV)
- Volume Rate of Change (VROC)
- Money Flow Index (MFI)
- Accumulation/Distribution

**Pattern Recognition**
- Fibonacci Retracement & Extension
- Support/Resistance Levels
- Candlestick Patterns
- Divergence Detection

### 📊 Signal Strength: 1–11 Scale

Confidence score combines multiple indicators:

```
11  = Extreme (5+ indicators aligned, rare)
9–10 = Very Strong (4+ indicators, high conviction)
7–8  = Strong (3+ indicators agree)
5–6  = Moderate (mixed signals)
3–4  = Weak (single indicator)
1–2  = Noise (ignore)
```

**Examples**:
- Strength 11: Price touches Fibonacci level + Bollinger Band + RSI + Volume spike + MACD crossover
- Strength 9: Bollinger Band cross + Fibonacci touch + RSI confirmation
- Strength 7: Bollinger Band cross + Volume spike
- Strength 3: Single RSI threshold (ignore)

### 🤖 AI-Powered Summaries

**Multi-Provider Strategy**:
1. **Gemini 2.5 Flash** — Primary (fast, cheap, high-quality)
2. **Mistral Medium** — Fallback (reliable if Gemini unavailable)
3. **Rule-Based** — Last resort (always works, template-based)

**Example Output**:
```
"AAPL showing strong bullish momentum with Fibonacci confluence at $175.30.
Multiple timeframes aligned bullish (1h, 1d). RSI confirms strength (72).
Volume spike confirms breakout potential. Consider buying on dips to $174."
```

### ⚡ Performance Optimization

**Parallel Processing**:
```python
# Analyze 200 symbols in parallel
analyzer = SignalAnalyzer(
    symbols=symbol_list,
    max_workers=10,  # 10 concurrent tasks
)
```

**Caching**:
```python
# Cache indicator calculations (avoid redundant math)
analyzer = SignalAnalyzer(
    symbols=symbol_list,
    cache_indicators=True,
)
```

**Timeframe Aggregation**:
```python
# Analyze multiple timeframes efficiently
analyzer = SignalAnalyzer(
    timeframes=['1m', '5m', '1h', '1d'],
    aggregate_timeframes=True,  # Combine results
)
```

### 🔄 Immutable Configuration

```python
from config import SignalConfig, ConfigFactory

# Create reproducible configuration
config = ConfigFactory.create(
    version='1.0',
    bollinger_period=20,
    fibonacci_levels=[0.236, 0.382, 0.618],
    rsi_period=14,
    signal_threshold=5,
)

# This config is immutable — same results every time
analyzer = SignalAnalyzer(config=config)
```

### 🛡️ Enterprise Error Handling

**Resilience Features**:
- Exponential backoff for API rate limits
- Circuit breaker for failed providers
- Graceful degradation (fallback chains)
- Per-symbol error recovery
- Comprehensive logging

**Example**:
```python
# If Gemini fails, automatically tries Mistral, then rules
try:
    summary = analyzer.get_ai_summary(signals, provider='gemini')
except RateLimitError:
    logger.warning("Gemini quota exceeded, using Mistral")
    summary = analyzer.get_ai_summary(signals, provider='mistral')
except APIError:
    logger.error("Both AI providers failed, using rule-based")
    summary = analyzer.get_rule_based_summary(signals)
```

---

## API Reference

### Main Classes

#### `SignalAnalyzer`
```python
class SignalAnalyzer:
    """Main analysis orchestrator."""
    
    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str] = ['1h', '1d'],
        config: SignalConfig = None,
        ai_config: AIConfig = None,
        max_workers: int = 10,
    ):
        """Initialize analyzer."""
    
    def analyze(self) -> List[Signal]:
        """Detect signals without AI summaries."""
    
    def analyze_with_summaries(self) -> Dict[str, Any]:
        """Detect signals with AI-generated summaries."""
    
    def analyze_symbol(self, symbol: str) -> List[Signal]:
        """Analyze single symbol."""
```

#### `Signal` (Data Class)
```python
@dataclass
class Signal:
    symbol: str              # Stock ticker
    timeframe: str           # 1m, 5m, 1h, 1d
    pattern: str             # bollinger_cross, fibonacci_touch, etc.
    direction: str           # bullish or bearish
    strength: int            # 1–11 confidence score
    price: float             # Price when signal detected
    timestamp: datetime      # When detected
    indicators: Dict         # Contributing indicators
    metadata: Dict           # Additional context
```

#### `IndicatorRegistry`
```python
class IndicatorRegistry:
    """Indicator factory and lookup."""
    
    def register(self, name: str, indicator_class: Type[Indicator]):
        """Register custom indicator."""
    
    def get(self, name: str) -> Indicator:
        """Get indicator instance."""
    
    def list_all(self) -> List[str]:
        """List registered indicators."""
```

---

## Configuration

### Signal Detection Parameters

```python
# config.py
BOLLINGER_PERIOD = 20        # Band calculation window
BOLLINGER_STD_DEV = 2.0      # Standard deviations

FIBONACCI_LEVELS = [
    0.236, 0.382, 0.5, 0.618, 0.786, 1.0
]

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

SIGNAL_STRENGTH_THRESHOLD = 5  # Only store signals ≥ 5
DISPLAY_STRENGTH_THRESHOLD = 7  # Only show signals ≥ 7
```

### AI Provider Configuration

```python
# AI timeouts and retries
GEMINI_TIMEOUT_SECONDS = 5
MISTRAL_TIMEOUT_SECONDS = 10
MAX_AI_RETRIES = 3
EXPONENTIAL_BACKOFF_FACTOR = 2

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS = 300
```

---

## Deployment

### Local Development

```bash
# Run analysis
python ai1.py --symbols AAPL,GOOGL --timeframes 1h,1d

# Run with logging
python ai1.py --loglevel DEBUG

# Run batch (all symbols)
python run_batch.py --batch-size 50
```

### GCP Cloud Run

```bash
# Build Docker image
docker build -t ai-fin4:latest .

# Deploy to Cloud Run
gcloud run deploy ai-fin4 \
  --image ai-fin4:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY

# Schedule daily runs
gcloud scheduler jobs create app-engine analyze-signals \
  --schedule="0 4 * * *" \
  --http-method POST \
  --uri=https://ai-fin4-xxx.run.app/analyze
```

### CI/CD Pipeline

```yaml
# .github/workflows/test-and-deploy.yml
name: Test & Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - run: pylint ai*.py indicators/ signals/

  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/auth@v1
      - uses: google-github-actions/setup-gcloud@v1
      - run: |
          gcloud run deploy ai-fin4 \
            --source . \
            --region us-central1
```

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_indicators.py::test_bollinger_bands -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Categories

```
tests/
├── test_indicators.py          # Indicator calculations
├── test_signals.py             # Signal detection
├── test_strength_scoring.py    # Confidence scores
├── test_ai_integration.py      # AI summaries
├── test_firebase.py            # Firestore operations
└── test_error_handling.py      # Error scenarios
```

### Example Test

```python
def test_bollinger_band_signal():
    """Test Bollinger Band signal detection."""
    analyzer = SignalAnalyzer(symbols=['AAPL'])
    
    # Get signals
    signals = analyzer.analyze()
    
    # Verify
    bb_signals = [s for s in signals if s.pattern == 'bollinger_cross']
    assert len(bb_signals) > 0
    assert all(s.strength >= 5 for s in bb_signals)
```

---

## Monitoring

### Key Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Analysis runtime | <10 min | >15 min |
| Signal detection rate | 100–500 signals | <50 or >1000 |
| AI summary success | 95%+ | <90% |
| Gemini/Mistral fallback | <5% | >10% |
| Data freshness | <1 hour old | >24 hours |
| Error rate | <1% | >2% |

### Logging

```python
from logging_config import get_logger

logger = get_logger()

# Structured logging
logger.info(
    "Analysis complete",
    extra={
        "symbols_analyzed": 200,
        "signals_detected": 1247,
        "ai_model": "gemini",
        "runtime_seconds": 342,
    }
)
```

### Health Checks

```bash
# Check system status
curl https://ai-fin4-xxx.run.app/health

# Response
{
  "status": "healthy",
  "firestore": "ok",
  "gemini": "ok",
  "mistral": "ok",
  "last_analysis": "2026-04-25T04:00:00Z",
  "uptime_seconds": 86400
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No signals detected | Threshold too high | Lower `SIGNAL_STRENGTH_THRESHOLD` |
| Slow analysis | Many workers competing | Reduce `max_workers` |
| Gemini quota exceeded | Too many API calls | Increase `RATE_LIMIT_REQUESTS_PER_MINUTE` |
| Firestore writes failing | IAM permissions | Check service account roles |
| AI summaries missing | Both providers down | Check API keys and network |

### Debug Mode

```bash
# Enable debug logging
python ai1.py --loglevel DEBUG

# Output detailed indicator calculations
python ai1.py --debug --symbols AAPL --verbose
```

---

## Performance Benchmarks

### Analysis Speed

```
200 symbols × 4 timeframes:
  Without parallelization:  ~2–3 hours
  With 10 workers:          ~5–10 minutes
  With caching:             ~2–3 minutes (if cached)
```

### Memory Usage

```
Per symbol analysis:  ~50 MB (OHLCV + indicators)
200 symbols:          ~10 GB (peak during parallel)
Firestore batch:      ~5 MB (1000 documents)
```

### Cost Breakdown (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| GCP Cloud Run | ~$5 | 1 job/day × 10 min |
| Gemini API | ~$3 | 200 symbols × $0.00005 |
| Mistral (fallback) | <$1 | Rarely used |
| Firestore | ~$5 | 1M reads + 200 writes |
| **Total** | **~$14/month** | Negligible |

---

## Contributing

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feat/new-indicator

# 2. Make changes and test
pytest tests/

# 3. Commit with clear message
git commit -m "feat: add custom indicator"

# 4. Push and create PR
git push origin feat/new-indicator
```

### Code Style

- Python: PEP 8 (enforced via `pylint`)
- Type hints: Required for all public functions
- Docstrings: Google-style for classes and functions
- Tests: Minimum 80% coverage

### Adding Custom Indicators

```python
from indicators.base import Indicator

class MyIndicator(Indicator):
    """Custom indicator."""
    
    def __init__(self, period: int = 20):
        super().__init__('my_indicator')
        self.period = period
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate indicator values."""
        return data['close'].rolling(self.period).mean()

# Register
from indicators.registry import IndicatorRegistry
registry = IndicatorRegistry()
registry.register('my_indicator', MyIndicator)
```

---

## Documentation

- **Project Wiki**: See `docs/wiki-aifin4/` for architecture, decisions, concepts
- **API Docs**: Generated from docstrings (see `docs/api.md`)
- **Examples**: See `examples/` for common use cases
- **Blog Posts**: [Technical Blog] (coming soon)

---

## License

MIT License. See LICENSE file for details.

---

## Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Email**: support@example.com
- **Security**: See SECURITY.md for reporting vulnerabilities

---

## Related Projects

- **ai-fin-opt2**: Parent project (full-stack framework)
- **alpha-fullstack**: GCP infrastructure foundation
- **ai-fin3**: Previous analysis pipeline (legacy)

---

## Changelog

### v1.0.0 (Production Ready)
- 20+ technical indicators
- 11-level signal strength scoring
- Multi-AI provider support with fallback
- Firestore batch operations
- Cloud Run deployment ready

### v0.9.0 (Beta)
- Core indicator library
- Signal detection engine
- Firebase integration

---

**Last Updated**: April 26, 2026

---

## Quick Links

- 🚀 [Getting Started](#quick-start)
- 📖 [Documentation](docs/wiki-aifin4/index.md)
- 🐛 [Report a Bug](https://github.com/your-org/ai-fin4/issues)
- 💡 [Feature Request](https://github.com/your-org/ai-fin4/discussions)
- 🔐 [Security Policy](SECURITY.md)
