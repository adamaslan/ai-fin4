# Claude Memory: Code Restructuring Plan

**Project:** Flexible Multi-Timeframe Signal Analyzer
**Created:** December 24, 2025
**Status:** AWAITING APPROVAL

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
**Status:** `[ ] PENDING`

Create `__init__.py` for each package:
- `analyzer/__init__.py`
- `data/__init__.py`
- `signals/__init__.py`
- `indicators/__init__.py`

### STEP 2: Move Indicator Files to indicators/
**Status:** `[ ] PENDING`

Move files:
- `base_ind.py` → `indicators/base.py`
- `momentum.py` → `indicators/momentum.py`
- `moving_averages.py` → `indicators/moving_averages.py`
- `registry.py` → `indicators/registry.py`
- `trend_volume.py` → `indicators/trend_volume.py`

### STEP 3: Move Signal Files to signals/
**Status:** `[ ] PENDING`

Move/rename files:
- `momentum-signals.py` → `signals/momentum_signals.py`
- `fibonacci.py` → `signals/fibonacci_signals.py`
- `validator-sig.py` → `signals/validator.py`

### STEP 4: Create analyzer/core.py (MultiTimeframeAnalyzer)
**Status:** `[ ] PENDING`

Create the refactored analyzer that:
- Injects DataProvider
- Injects IndicatorRegistry
- Injects SignalAggregator
- Orchestrates the pipeline
- Handles errors gracefully

### STEP 5: Move analyzer.py to analyzer/pipeline.py
**Status:** `[ ] PENDING`

Move:
- `analyzer.py` → `analyzer/pipeline.py`

Update imports to use new locations.

### STEP 6: Integrate AI Modules (ai1.py, ai2.py)
**Status:** `[ ] PENDING`

Options:
- A) Keep as top-level modules (simpler)
- B) Create `ai/` package with themes.py, learning.py
- C) Integrate into analyzer/pipeline.py

---

## TARGET FILE STRUCTURE

```
ai-fin4/
├── analyzer/
│   ├── __init__.py           # Exports: MultiTimeframeAnalyzer, AnalysisPipeline
│   ├── core.py               # MultiTimeframeAnalyzer (refactored)
│   └── pipeline.py           # AnalysisPipeline (from analyzer.py)
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

## APPROVAL CHECKLIST

Before I begin, please confirm:

- [ ] **Step 1-3:** Approve reorganizing files into packages
- [ ] **Step 4:** Approve creating new `analyzer/core.py`
- [ ] **Step 5:** Approve moving `analyzer.py`
- [ ] **Step 6:** Choose AI integration approach (A/B/C)
- [ ] **Overall:** Ready to proceed step-by-step

---

## HOW PROGRESS WILL BE TRACKED

After each step:
1. I will update this file with `[x] COMPLETE` status
2. I will show you what was done
3. You can approve or request changes
4. I proceed to next step only after your approval

---

## NEXT ACTION

**Awaiting your review and approval to proceed with Step 1.**

Reply with:
- "Approve Step 1" to begin
- "Modify plan" if you want changes
- Questions if anything is unclear
