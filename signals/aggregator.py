"""
Signal aggregator and orchestrator.

Manages signal detection across all detectors, handles deduplication,
ranking, and filtering.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import pandas as pd
from signals.base import Signal, SignalDetector, SignalFilter, SignalSorter
from logging_config import get_logger
from exceptions import SignalDetectionError

logger = get_logger()


# ============ AGGREGATION RESULT ============


@dataclass
class AggregationResult:
    """Result from signal aggregation."""

    signals: List[Signal]
    """All detected signals."""

    signal_count: int
    """Total number of signals."""

    bullish_count: int
    """Count of bullish signals."""

    bearish_count: int
    """Count of bearish signals."""

    neutral_count: int
    """Count of neutral signals."""

    by_category: Dict[str, List[Signal]]
    """Signals grouped by category."""

    by_strength: Dict[str, List[Signal]]
    """Signals grouped by strength."""

    duplicates_removed: int
    """Number of duplicate signals removed."""

    def __str__(self) -> str:
        """Return formatted summary."""
        return (
            f"Signals: {self.signal_count} "
            f"(↑{self.bullish_count} ↓{self.bearish_count} →{self.neutral_count})"
        )


# ============ SIGNAL AGGREGATOR ============


class SignalAggregator:
    """
    Orchestrates signal detection across all detectors.

    Collects signals from multiple detectors, deduplicates, ranks,
    and provides structured results.
    """

    def __init__(self, timeframe: str = "unknown"):
        """
        Initialize aggregator.

        Args:
            timeframe: Timeframe being analyzed (for signal context).
        """
        self.timeframe = timeframe
        self.detectors: List[SignalDetector] = []

    def add_detector(self, detector: SignalDetector) -> None:
        """
        Add a signal detector to the aggregator.

        Args:
            detector: SignalDetector instance to add.
        """
        self.detectors.append(detector)
        logger.debug(f"Added signal detector: {detector.metadata.name}")

    def add_detectors(self, detectors: List[SignalDetector]) -> None:
        """
        Add multiple detectors.

        Args:
            detectors: List of SignalDetector instances.
        """
        for detector in detectors:
            self.add_detector(detector)

    def detect(self, df: pd.DataFrame) -> AggregationResult:
        """
        Execute all detectors and aggregate signals.

        Args:
            df: Market data with indicators calculated.

        Returns:
            AggregationResult with all signals and statistics.
        """
        logger.info(f"Aggregating signals from {len(self.detectors)} detectors")

        all_signals = []
        detector_count = 0
        errors = []

        # Execute each detector
        for detector in self.detectors:
            try:
                logger.debug(f"Executing detector: {detector.metadata.name}")
                signals = detector.execute(df)
                all_signals.extend(signals)
                detector_count += 1

            except SignalDetectionError as e:
                logger.warning(f"Detector error ({detector.metadata.name}): {str(e)}")
                errors.append((detector.metadata.name, str(e)))
            except Exception as e:
                logger.error(f"Unexpected error in {detector.metadata.name}: {str(e)}")
                errors.append((detector.metadata.name, str(e)))

        # Set timeframe on all signals
        for signal in all_signals:
            object.__setattr__(signal, "timeframe", self.timeframe)

        logger.info(f"Collected {len(all_signals)} signals from {detector_count} detectors")

        # Deduplicate
        unique_signals = self._deduplicate(all_signals)
        duplicates_removed = len(all_signals) - len(unique_signals)

        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate signals")

        # Sort by strength and confidence
        sorted_signals = SignalSorter.by_strength(unique_signals)
        sorted_signals = SignalSorter.by_confidence(sorted_signals, ascending=False)

        # Generate result
        result = self._build_result(sorted_signals, duplicates_removed)

        logger.info(f"Aggregation complete: {result}")

        return result

    def _deduplicate(self, signals: List[Signal]) -> List[Signal]:
        """
        Remove duplicate or near-duplicate signals.

        Considers signals duplicate if they have the same:
        - Category
        - Strength
        - Name (with small variations allowed)

        Args:
            signals: List of signals to deduplicate.

        Returns:
            Deduplicated list of signals.
        """
        seen: Set[str] = set()
        unique = []

        for signal in signals:
            # Create signature for deduplication
            # Use category + strength + approximate name
            signature = f"{signal.category}_{signal.strength}_{signal.name[:20]}"

            if signature not in seen:
                seen.add(signature)
                unique.append(signal)

        return unique

    def _build_result(
        self, signals: List[Signal], duplicates_removed: int
    ) -> AggregationResult:
        """
        Build aggregation result with statistics.

        Args:
            signals: Sorted list of signals.
            duplicates_removed: Count of removed duplicates.

        Returns:
            AggregationResult with all statistics.
        """
        # Count by strength
        bullish = len(SignalFilter.by_bullish(signals))
        bearish = len(SignalFilter.by_bearish(signals))
        neutral = len(signals) - bullish - bearish

        # Group by category
        by_category = SignalSorter.by_category(signals)

        # Group by strength
        by_strength: Dict[str, List[Signal]] = {}
        for signal in signals:
            if signal.strength not in by_strength:
                by_strength[signal.strength] = []
            by_strength[signal.strength].append(signal)

        return AggregationResult(
            signals=signals,
            signal_count=len(signals),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            by_category=by_category,
            by_strength=by_strength,
            duplicates_removed=duplicates_removed,
        )


# ============ DETECTOR FACTORY ============


class DetectorFactory:
    """
    Factory for creating pre-configured detector combinations.

    Provides pre-made combinations of detectors for different strategies.
    """

    @staticmethod
    def create_basic_detectors() -> List[SignalDetector]:
        """
        Create basic detector set.

        Includes: MA crossover, RSI, MACD

        Returns:
            List of SignalDetector instances.
        """
        from signals.ma_signals import MovingAverageCrossoverDetector
        from signals.momentum_signals import RSISignalDetector, MACDSignalDetector

        return [
            MovingAverageCrossoverDetector(fast_period=10, slow_period=20),
            RSISignalDetector(period=14),
            MACDSignalDetector(),
        ]

    @staticmethod
    def create_comprehensive_detectors() -> List[SignalDetector]:
        """
        Create comprehensive detector set.

        Includes: MA crossover, MA positioning, RSI, MACD, Stochastic, Fibonacci

        Returns:
            List of SignalDetector instances.
        """
        from signals.ma_signals import (
            MovingAverageCrossoverDetector,
            MovingAveragePositioningDetector,
            MovingAverageRibbonDetector,
        )
        from signals.momentum_signals import (
            RSISignalDetector,
            MACDSignalDetector,
            StochasticSignalDetector,
        )
        from signals.fibonacci_signals import FibonacciSignalDetector

        return [
            MovingAverageCrossoverDetector(fast_period=10, slow_period=20),
            MovingAveragePositioningDetector(periods=(20, 50, 200)),
            MovingAverageRibbonDetector(),
            RSISignalDetector(period=14),
            MACDSignalDetector(),
            StochasticSignalDetector(period=14),
            FibonacciSignalDetector(window=50),
        ]

    @staticmethod
    def create_intraday_detectors() -> List[SignalDetector]:
        """
        Create intraday-optimized detector set.

        Fast indicators for 5m-1h timeframes.

        Returns:
            List of SignalDetector instances.
        """
        from signals.ma_signals import MovingAverageCrossoverDetector
        from signals.momentum_signals import RSISignalDetector, MACDSignalDetector

        return [
            MovingAverageCrossoverDetector(fast_period=5, slow_period=10),
            RSISignalDetector(period=7, oversold=25, overbought=75),
            MACDSignalDetector(),
        ]

    @staticmethod
    def create_swing_detectors() -> List[SignalDetector]:
        """
        Create swing-trading detector set.

        Medium-term indicators for 1h-1d timeframes.

        Returns:
            List of SignalDetector instances.
        """
        from signals.ma_signals import (
            MovingAverageCrossoverDetector,
            MovingAverageRibbonDetector,
        )
        from signals.momentum_signals import (
            RSISignalDetector,
            MACDSignalDetector,
            StochasticSignalDetector,
        )

        return [
            MovingAverageCrossoverDetector(fast_period=10, slow_period=30),
            MovingAverageRibbonDetector(periods=(10, 20, 50, 100, 200)),
            RSISignalDetector(period=14),
            MACDSignalDetector(),
            StochasticSignalDetector(period=14),
        ]

    @staticmethod
    def create_trend_detectors() -> List[SignalDetector]:
        """
        Create trend-following detector set.

        Focused on long-term trend confirmation.

        Returns:
            List of SignalDetector instances.
        """
        from signals.ma_signals import MovingAverageRibbonDetector
        from signals.momentum_signals import MACDSignalDetector
        from signals.fibonacci_signals import FibonacciSignalDetector

        return [
            MovingAverageRibbonDetector(periods=(20, 50, 100, 200)),
            MACDSignalDetector(),
            FibonacciSignalDetector(window=100),
        ]


# ============ SIGNAL AGGREGATOR WITH FILTERING ============


class FilteredSignalAggregator(SignalAggregator):
    """
    Signal aggregator with built-in filtering.

    Extends SignalAggregator with filtering and quality control options.
    """

    def __init__(
        self,
        timeframe: str = "unknown",
        min_confidence: float = 0.0,
        exclude_neutral: bool = False,
    ):
        """
        Initialize filtered aggregator.

        Args:
            timeframe: Timeframe being analyzed.
            min_confidence: Minimum confidence threshold (0.0 to 1.0).
            exclude_neutral: Exclude neutral signals if True.
        """
        super().__init__(timeframe)
        self.min_confidence = min_confidence
        self.exclude_neutral = exclude_neutral

    def detect(self, df: pd.DataFrame) -> AggregationResult:
        """
        Execute detection with filtering applied.

        Args:
            df: Market data with indicators.

        Returns:
            AggregationResult with filters applied.
        """
        # Get aggregated signals
        result = super().detect(df)

        # Apply filters
        filtered_signals = result.signals.copy()

        # Filter by confidence
        if self.min_confidence > 0:
            filtered_signals = SignalFilter.by_confidence(
                filtered_signals, self.min_confidence
            )
            logger.info(
                f"Filtered by confidence ({self.min_confidence}): "
                f"{len(result.signals)} → {len(filtered_signals)}"
            )

        # Exclude neutral
        if self.exclude_neutral:
            filtered_signals = [s for s in filtered_signals if not s.is_neutral()]
            logger.info(
                f"Excluded neutral: {len(result.signals)} → {len(filtered_signals)}"
            )

        # Rebuild result with filtered signals
        return self._build_result(filtered_signals, result.duplicates_removed)