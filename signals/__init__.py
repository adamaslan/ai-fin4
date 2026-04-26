"""
Signals package.

Provides signal detection, aggregation, and validation.

Exports:
    Signal: Frozen dataclass representing a trading signal.
    SignalStrength: Constants for signal strength levels.
    SignalDetector: Abstract base class for signal detectors.
    SignalAggregator: Orchestrates multiple detectors.
    SignalFilter: Filters signals by various criteria.
    SignalSorter: Sorts signals by confidence, strength, etc.
    SignalValidator: Validates signal integrity.

Detectors:
    MovingAverageCrossoverDetector: MA crossover signals.
    MovingAveragePositioningDetector: Price vs MA positioning.
    RSISignalDetector: RSI overbought/oversold signals.
    MACDSignalDetector: MACD crossover signals.
    StochasticSignalDetector: Stochastic oscillator signals.
    FibonacciSignalDetector: Fibonacci level signals.
"""

from __future__ import annotations

from signals.base import (
    Signal,
    SignalStrength,
    SignalDetector,
    SignalDetectorMetadata,
    SignalFilter,
    SignalSorter,
)
from signals.aggregator import SignalAggregator, AggregationResult, DetectorFactory

from signals.ma_signals import (
    MovingAverageCrossoverDetector,
    MovingAveragePositioningDetector,
)

from signals.momentum_signals import (
    RSISignalDetector,
    MACDSignalDetector,
    StochasticSignalDetector,
)
from signals.fibonacci_signals import FibonacciLevels, FibonacciSignalDetector
from signals.validator import (
    SignalValidator,
    ContradictionDetector,
    QualityScorer,
    SignalQualityPipeline,
)

__all__ = [
    # Base classes
    "Signal",
    "SignalStrength",
    "SignalDetector",
    "SignalDetectorMetadata",
    "SignalFilter",
    "SignalSorter",
    # Aggregation
    "SignalAggregator",
    "AggregationResult",
    "DetectorFactory",
    # MA Detectors
    "MovingAverageCrossoverDetector",
    "MovingAveragePositioningDetector",
    # Momentum Detectors
    "RSISignalDetector",
    "MACDSignalDetector",
    "StochasticSignalDetector",
    # Fibonacci
    "FibonacciLevels",
    "FibonacciSignalDetector",
    # Validation
    "SignalValidator",
    "ContradictionDetector",
    "QualityScorer",
    "SignalQualityPipeline",
]
