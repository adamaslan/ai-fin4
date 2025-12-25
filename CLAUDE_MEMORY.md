# Claude Memory: Code Restructuring Plan

**Project:** Flexible Multi-Timeframe Signal Analyzer
**Created:** December 24, 2025
**Status:** COMPLETE (All 6 steps finished)

---

## SAVED CORE DESIGN PATTERNS (18 Patterns)

### Pattern 1: Single Responsibility Principle (SRP)
Each class/function has ONE clear purpose. No god classes.

### Pattern 2: Law of Demeter
Only interact with immediate collaborators. Avoid `obj.a.b.c` chains.

### Pattern 3: Early Returns (Guard Clauses)
Avoid deep nesting. Return early on invalid conditions.

### Pattern 4: Dependency Injection
Pass dependencies explicitly. No hidden globals.

### Pattern 5: Immutable Data Structures
Use `@dataclass(frozen=True)` where appropriate.

### Pattern 6: Custom Exception Hierarchy
Domain-specific exceptions (AnalyzerError, DataFetchError, etc.)

### Pattern 7: Type Hints Throughout
100% type annotation coverage.

### Pattern 8: Composition over Inheritance
Prefer flexible composition to deep inheritance trees.

### Pattern 9: Protocol/ABC
Use `typing.Protocol` for interfaces.

### Pattern 10: Context Managers
Proper resource management with `with` statements.

### Pattern 11: Specific Exception Handling
Catch specific types, not bare `except:`.

### Pattern 12: Meaningful Names
Self-documenting code with clear variable/function names.

### Pattern 13: Docstrings
Google-style docstrings on all public functions.

### Pattern 14: Code Decomposition
Break complex functions into focused ones (<30 lines).

### Pattern 15: Logging Module
Use `logging`, not `print()` for production.

### Pattern 16: No Magic Numbers
Use named constants for all numeric values.

### Pattern 17: Collection Types
Choose appropriate collections (list, set, dict, deque).

### Pattern 18: Async/Await
For I/O-bound operations (data fetching).

---

## CURRENT CODEBASE STATUS

### Existing Files (Root Level)
| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `ai1.py` | ~780 | AI Themes 1-10 (Signal Summarization, Confluence, etc.) | EXISTS |
| `ai2.py` | ~655 | AI Themes 11-25 (Alerts, Learning, Position Sizing) | EXISTS |
| `analyzer.py` | ~400 | AnalysisPipeline | EXISTS |
| `base_ind.py` | ~400 | Indicator Base Classes | EXISTS |
| `config.py` | ~430 | SignalConfig & ConfigFactory | EXISTS |
| `exceptions.py` | ~300 | Custom Exception Hierarchy | EXISTS |
| `exporters.py` | ~440 | JSON/Markdown/CSV Exporters | EXISTS |
| `fibonacci.py` | ~560 | Fibonacci Signal Detector | EXISTS |
| `logging_config.py` | ~270 | LoggerConfig | EXISTS |
| `momentum.py` | ~400 | RSI, MACD, Stochastic Indicators | EXISTS |
| `momentum-signals.py` | ~280 | Momentum Signal Detectors | EXISTS |
| `moving_averages.py` | ~340 | SMA, EMA, Crossover Indicators | EXISTS |
| `registry.py` | ~360 | IndicatorRegistry & Factory | EXISTS |
| `trend_volume.py` | ~300 | ATR, ADX, OBV Indicators | EXISTS |
| `types.py` | ~240 | Type Aliases & TypedDicts | EXISTS |

### Existing Directories
| Directory | Files | Status |
|-----------|-------|--------|
| `analyzer/` | EMPTY | NEEDS: core.py, __init__.py |
| `data/` | provider.py, validator.py | NEEDS: __init__.py |
| `signals/` | base.py, aggregator.py, ma_signals.py, validator-sig.py | NEEDS: __init__.py |
| `indicators/` | EMPTY | NEEDS: Move base_ind.py, momentum.py, moving_averages.py, registry.py, trend_volume.py |
| `docs/` | refactor.md | OK |

---

## RESTRUCTURING PLAN (6 Steps)

### STEP 1: Create Module __init__.py Files
**Status:** `[x] COMPLETE`

Created `__init__.py` for each package:
- `analyzer/__init__.py` - Exports MultiTimeframeAnalyzer, AnalysisPipeline
- `data/__init__.py` - Exports DataProvider, YFinanceProvider, validators
- `signals/__init__.py` - Exports Signal, SignalDetector, aggregators
- `indicators/__init__.py` - Exports IndicatorBase, registry, all indicators

### STEP 2: Move Indicator Files to indicators/
**Status:** `[x] COMPLETE`

Moved files (using git mv to preserve history):
- `base_ind.py` → `indicators/base.py`
- `momentum.py` → `indicators/momentum.py`
- `moving_averages.py` → `indicators/moving_averages.py`
- `registry.py` → `indicators/registry.py`
- `trend_volume.py` → `indicators/trend_volume.py`

Updated `indicators/__init__.py` with all imports enabled.

### STEP 3: Move Signal Files to signals/
**Status:** `[x] COMPLETE`

Moved/renamed files:
- `momentum-signals.py` → `signals/momentum_signals.py`
- `fibonacci.py` → `signals/fibonacci_signals.py`

Fixed misplaced files (swapped content):
- Signal validators now in `signals/validator.py` (SignalValidator, ContradictionDetector, QualityScorer)
- Data validators now in `data/validator.py` (MarketDataValidator, MarketDataCleaner)
- Momentum indicators now in `indicators/momentum.py` (RSI, MACD, Stochastic)
- Momentum detectors now in `signals/momentum_signals.py` (RSISignalDetector, etc.)

Updated all `__init__.py` files with correct imports.

### STEP 4: Create analyzer/core.py (MultiTimeframeAnalyzer)
**Status:** `[x] COMPLETE`

Created `analyzer/core.py` (~350 lines) with:
- `AnalysisResult` frozen dataclass with summary, to_dict()
- `MultiTimeframeAnalyzer` class with dependency injection:
  - Injects DataProvider (default: YFinanceProvider)
  - Injects IndicatorGroup (via IndicatorFactory)
  - Injects SignalAggregator (via DetectorFactory)
  - Injects SignalQualityPipeline
- Methods: `fetch_data()`, `calculate_indicators()`, `detect_signals()`
- Guard clauses for early validation
- Clean orchestration logic only (~150 lines)
- All 18 design patterns applied

### STEP 5: Move analyzer.py to analyzer/pipeline.py
**Status:** `[x] COMPLETE`

Moved with git mv:
- `analyzer.py` → `analyzer/pipeline.py`

Updated:
- Removed debug comment from pipeline.py
- Updated `analyzer/__init__.py` to export all classes:
  - MultiTimeframeAnalyzer, AnalysisResult (from core)
  - AnalysisPipeline, StepResult, analyze_symbol, analyze_multiple (from pipeline)

### STEP 6: Integrate AI Modules into Pipeline (Option C)
**Status:** `[x] COMPLETE`

Created `analyzer/ai_integration.py` (~300 lines):
- `AIAnalysisResult` dataclass with all AI insights
- `AIAnalyzer` class wrapping all 25 AI themes from ai1.py and ai2.py
- `create_ai_analyzer()` factory function
- Safe error handling for each AI component

Updated `analyzer/pipeline.py`:
- Added `enable_ai` parameter to AnalysisPipeline
- Added `_step_ai_analysis()` method
- Created `EnhancedAnalysisResult` combining base + AI results
- Added `analyze_with_ai()` convenience function
- AI failures are non-fatal (pipeline continues)

Updated `analyzer/__init__.py`:
- Exports all AI integration classes
- Graceful fallback if AI modules unavailable

---

## TARGET FILE STRUCTURE

```
ai-fin4/
├── analyzer/
│   ├── __init__.py           # Exports: All analyzer classes + AI
│   ├── core.py               # MultiTimeframeAnalyzer, AnalysisResult
│   ├── pipeline.py           # AnalysisPipeline, EnhancedAnalysisResult
│   └── ai_integration.py     # AIAnalyzer, AIAnalysisResult (NEW)
├── data/
│   ├── __init__.py           # Exports: DataProvider, YFinanceProvider
│   ├── provider.py           # Data fetching
│   └── validator.py          # Data validation
├── indicators/
│   ├── __init__.py           # Exports: IndicatorRegistry, all indicators
│   ├── base.py               # IndicatorBase (from base_ind.py)
│   ├── momentum.py           # RSI, MACD, Stochastic
│   ├── moving_averages.py    # SMA, EMA, Crossover
│   ├── registry.py           # IndicatorRegistry
│   └── trend_volume.py       # ATR, ADX, OBV
├── signals/
│   ├── __init__.py           # Exports: SignalAggregator, all detectors
│   ├── aggregator.py         # SignalAggregator
│   ├── base.py               # Signal, SignalDetector
│   ├── fibonacci_signals.py  # FibonacciSignalDetector (from fibonacci.py)
│   ├── ma_signals.py         # MovingAverageCrossoverDetector
│   ├── momentum_signals.py   # RSI, MACD signal detectors
│   └── validator.py          # SignalValidator (from validator-sig.py)
├── ai1.py                    # AI Themes 1-10
├── ai2.py                    # AI Themes 11-25
├── config.py                 # SignalConfig
├── exceptions.py             # Custom exceptions
├── exporters.py              # Export classes
├── logging_config.py         # Logger configuration
├── types.py                  # Type definitions
├── main.py                   # Entry point (NEW)
├── CLAUDE_MEMORY.md          # This file
└── docs/
    └── refactor.md           # Original plan
```

---

## COMPLETION CHECKLIST

All steps completed:

- [x] **Step 1:** Created `__init__.py` for all packages
- [x] **Step 2:** Moved indicator files to `indicators/`
- [x] **Step 3:** Moved signal files to `signals/`
- [x] **Step 4:** Created `analyzer/core.py` with MultiTimeframeAnalyzer
- [x] **Step 5:** Moved `analyzer.py` to `analyzer/pipeline.py`
- [x] **Step 6:** Integrated AI modules (Option C) into pipeline

---

## RESTRUCTURING COMPLETE

**Date Completed:** December 24, 2025

### Summary of Changes

| Category | Files Created/Modified |
|----------|----------------------|
| Packages | 4 `__init__.py` files created |
| Indicators | 5 files moved to `indicators/` |
| Signals | 3 files moved to `signals/` |
| Analyzer | 3 files in `analyzer/` (core, pipeline, ai_integration) |

### New Usage

```python
# Basic analysis
from analyzer import analyze_symbol
result = analyze_symbol('SPY', interval='1h')
print(result.summary)

# With AI
from analyzer import analyze_with_ai
result = analyze_with_ai('SPY', interval='1d')
print(result.ai_result.trading_recommendation)

# Full pipeline control
from analyzer import AnalysisPipeline
pipeline = AnalysisPipeline(
    symbol='AAPL',
    interval='1h',
    enable_ai=True,
    indicator_factory='momentum',
    detector_factory='trend',
)
result = pipeline.run()
```

### Design Patterns Applied

All 18 patterns from the original plan:
1. Single Responsibility Principle
2. Law of Demeter
3. Early Returns (Guard Clauses)
4. Dependency Injection
5. Immutable Data Structures
6. Custom Exception Hierarchy
7. Type Hints Throughout
8. Composition over Inheritance
9. Protocol/ABC Interfaces
10. Context Managers
11. Specific Exception Handling
12. Meaningful Names
13. Docstrings (Google-style)
14. Code Decomposition
15. Logging Module
16. No Magic Numbers
17. Collection Types
18. Async/Await (where applicable)

---

## VERIFICATION (December 24, 2025)

### Syntax Check
All 20 Python files pass `py_compile`:
- `analyzer/`: 4 files ✓
- `indicators/`: 6 files ✓
- `signals/`: 7 files ✓
- `data/`: 3 files ✓

### Pattern Compliance Fixes
Fixed 8 bare `except:` clauses (Pattern 11 violation):
- `indicators/registry.py:204` → `except Exception:`
- `indicators/moving_averages.py:118,226,350` → `except (TypeError, ValueError):`
- `signals/momentum_signals.py:138,264,402` → `except (TypeError, ValueError):`
- `signals/fibonacci_signals.py:512` → `except (TypeError, ValueError):`

### Verification Results
- ✓ No `print()` statements (only in docstring examples)
- ✓ No bare `except:` clauses
- ✓ No TODO/FIXME/HACK comments
- ✓ All files have module docstrings
- ✓ Uses logging module throughout
