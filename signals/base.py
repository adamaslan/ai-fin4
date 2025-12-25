"""
Base classes for signal detection.

Provides structures and interfaces for detecting and managing trading signals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
import pandas as pd
from logging_config import get_logger
from exceptions import SignalDetectionError
from type_defs import SignalInfo

logger = get_logger()


# ============ SIGNAL STRENGTH CONSTANTS ============

class SignalStrength:
    """Signal strength levels."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    STRONG_BULLISH = "STRONG BULLISH"
    STRONG_BEARISH = "STRONG BEARISH"
    NEUTRAL = "NEUTRAL"
    EXTREME_BULLISH = "EXTREME BULLISH"
    EXTREME_BEARISH = "EXTREME BEARISH"
    TRENDING = "TRENDING"
    SIGNIFICANT = "SIGNIFICANT"
    MODERATE = "MODERATE"
    WEAK = "WEAK"

    @staticmethod
    def is_bullish(strength: str) -> bool:
        """Check if strength indicates bullish signal."""
        return "BULLISH" in strength.upper()

    @staticmethod
    def is_bearish(strength: str) -> bool:
        """Check if strength indicates bearish signal."""
        return "BEARISH" in strength.upper()

    @staticmethod
    def is_neutral(strength: str) -> bool:
        """Check if strength is neutral."""
        return strength == SignalStrength.NEUTRAL

    @staticmethod
    def get_bullish_strengths() -> Set[str]:
        """Get all bullish signal strengths."""
        return {
            SignalStrength.BULLISH,
            SignalStrength.STRONG_BULLISH,
            SignalStrength.EXTREME_BULLISH,
        }

    @staticmethod
    def get_bearish_strengths() -> Set[str]:
        """Get all bearish signal strengths."""
        return {
            SignalStrength.BEARISH,
            SignalStrength.STRONG_BEARISH,
            SignalStrength.EXTREME_BEARISH,
        }


# ============ SIGNAL DATA CLASS ============


@dataclass(frozen=True)
class Signal:
    """
    Immutable signal detection result.

    Represents a single detected trading signal with all context.
    """

    name: str
    """Signal identifier/name."""

    category: str
    """Signal category (MA_CROSS, RSI, MACD, etc.)."""

    strength: str
    """Signal strength (BULLISH, BEARISH, STRONG BULLISH, etc.)."""

    description: str
    """Human-readable description."""

    timeframe: str
    """Timeframe on which signal was detected."""

    value: Optional[float] = None
    """Numeric value associated with signal."""

    confidence: float = field(default=0.5)
    """Confidence score (0.0 to 1.0)."""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the signal was detected."""

    indicator_name: Optional[str] = None
    """Name of indicator that generated signal."""

    details: Dict[str, Any] = field(default_factory=dict)
    """Additional context and details."""

    trading_implication: Optional[str] = None
    """Suggested trading action."""

    def to_dict(self) -> SignalInfo:
        """
        Convert to dictionary format.

        Returns:
            Dictionary representation of signal.
        """
        return {
            "signal": self.name,
            "category": self.category,
            "strength": self.strength,
            "description": self.description,
            "timeframe": self.timeframe,
            "value": self.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "indicator_name": self.indicator_name,
            "details": self.details,
            "trading_implication": self.trading_implication,
        }

    def is_bullish(self) -> bool:
        """Check if signal is bullish."""
        return SignalStrength.is_bullish(self.strength)

    def is_bearish(self) -> bool:
        """Check if signal is bearish."""
        return SignalStrength.is_bearish(self.strength)

    def is_neutral(self) -> bool:
        """Check if signal is neutral."""
        return SignalStrength.is_neutral(self.strength)

    def __str__(self) -> str:
        """Return formatted signal string."""
        return f"{self.name} ({self.strength}) - {self.description}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"Signal(name={self.name}, strength={self.strength}, "
            f"confidence={self.confidence:.2f})"
        )


# ============ SIGNAL DETECTOR BASE CLASS ============


class SignalDetector(ABC):
    """
    Abstract base class for signal detection.

    All signal detectors inherit from this class and implement
    the `detect()` method. Provides common validation and error handling.

    Example:
        >>> class MySignalDetector(SignalDetector):
        ...     @property
        ...     def metadata(self) -> SignalDetectorMetadata:
        ...         return SignalDetectorMetadata(
        ...             name="My Detector",
        ...             category="custom",
        ...             required_indicators=["MA_20"],
        ...             description="Custom signal detection"
        ...         )
        ...
        ...     def detect(self, df: pd.DataFrame) -> List[Signal]:
        ...         signals = []
        ...         # Detection logic here
        ...         return signals
    """

    @property
    @abstractmethod
    def metadata(self) -> SignalDetectorMetadata:
        """
        Get metadata about this detector.

        Must be implemented by subclasses.

        Returns:
            SignalDetectorMetadata with detector information.
        """
        pass

    def validate_input(self, df: pd.DataFrame) -> None:
        """
        Validate input data meets requirements.

        Checks:
        - DataFrame is not empty
        - Has required columns

        Args:
            df: Market data to validate.

        Raises:
            SignalDetectionError: If validation fails.
        """
        meta = self.metadata

        # Check empty
        if df.empty:
            raise SignalDetectionError(
                f"Cannot detect {meta.name}: data is empty",
                detector=meta.name,
            )

        # Check required columns
        required_cols = self._get_required_columns()
        missing = required_cols - set(df.columns)

        if missing:
            raise SignalDetectionError(
                f"Cannot detect {meta.name}: missing columns {missing}",
                detector=meta.name,
            )

    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect signals in market data.

        Must be implemented by subclasses. Should:
        1. Validate input data
        2. Analyze indicators/prices
        3. Generate Signal objects
        4. Return list of signals

        Args:
            df: Market data with indicators calculated.

        Returns:
            List of detected Signal objects.

        Raises:
            SignalDetectionError: If detection fails.
        """
        pass

    def execute(self, df: pd.DataFrame) -> List[Signal]:
        """
        Execute signal detection with validation.

        Public method that validates input and handles errors.
        Preferred over direct `detect()` call.

        Args:
            df: Market data DataFrame.

        Returns:
            List of detected signals.

        Raises:
            SignalDetectionError: If detection fails.

        Example:
            >>> detector = MySignalDetector()
            >>> signals = detector.execute(market_data)
        """
        meta = self.metadata

        try:
            # Validate input
            self.validate_input(df)

            # Detect signals
            logger.debug(f"Detecting {meta.name}")
            signals = self.detect(df)

            logger.debug(f"Detected {len(signals)} signals from {meta.name}")
            return signals

        except SignalDetectionError:
            raise
        except Exception as e:
            raise SignalDetectionError(
                f"Error detecting {meta.name}: {str(e)}",
                detector=meta.name,
                exception=e,
            ) from e

    def _get_required_columns(self) -> Set[str]:
        """
        Get required columns from metadata.

        Returns:
            Set of required column names.
        """
        meta = self.metadata
        required = {"Open", "High", "Low", "Close", "Volume"}
        required.update(meta.required_indicators)
        return required

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.metadata)

    def __repr__(self) -> str:
        """Return detailed representation."""
        meta = self.metadata
        return f"{meta.name} (category={meta.category})"


# ============ SIGNAL DETECTOR METADATA ============


@dataclass(frozen=True)
class SignalDetectorMetadata:
    """
    Metadata about a signal detector.

    Provides information about what a detector does and requires.
    """

    name: str
    """Human-readable name of the detector."""

    category: str
    """Detector category (ma_cross, rsi, macd, etc.)."""

    required_indicators: tuple = ()
    """Tuple of indicator column names required (e.g., ('SMA_20', 'RSI_14'))."""

    description: str = ""
    """Description of what signals this detector finds."""

    signal_categories: tuple = ()
    """Tuple of signal categories this detector can produce."""

    def __str__(self) -> str:
        """Return formatted metadata string."""
        return f"{self.name} ({self.category})"


# ============ SIGNAL FILTERS ============


class SignalFilter:
    """
    Filters signals based on criteria.

    Can filter by strength, confidence, category, etc.
    """

    @staticmethod
    def by_strength(signals: List[Signal], strength: str) -> List[Signal]:
        """
        Filter signals by strength.

        Args:
            signals: List of signals to filter.
            strength: Strength to match (e.g., 'BULLISH').

        Returns:
            Filtered list of signals.
        """
        return [s for s in signals if s.strength == strength]

    @staticmethod
    def by_bullish(signals: List[Signal]) -> List[Signal]:
        """
        Get all bullish signals.

        Args:
            signals: List of signals.

        Returns:
            Bullish signals only.
        """
        return [s for s in signals if s.is_bullish()]

    @staticmethod
    def by_bearish(signals: List[Signal]) -> List[Signal]:
        """
        Get all bearish signals.

        Args:
            signals: List of signals.

        Returns:
            Bearish signals only.
        """
        return [s for s in signals if s.is_bearish()]

    @staticmethod
    def by_category(signals: List[Signal], category: str) -> List[Signal]:
        """
        Filter signals by category.

        Args:
            signals: List of signals.
            category: Category to match (e.g., 'MACD').

        Returns:
            Filtered signals.
        """
        return [s for s in signals if s.category == category]

    @staticmethod
    def by_confidence(signals: List[Signal], min_confidence: float) -> List[Signal]:
        """
        Filter signals by confidence threshold.

        Args:
            signals: List of signals.
            min_confidence: Minimum confidence (0.0 to 1.0).

        Returns:
            Signals meeting confidence threshold.
        """
        return [s for s in signals if s.confidence >= min_confidence]

    @staticmethod
    def by_indicator(signals: List[Signal], indicator_name: str) -> List[Signal]:
        """
        Filter signals by indicator name.

        Args:
            signals: List of signals.
            indicator_name: Indicator name to match.

        Returns:
            Signals from that indicator.
        """
        return [s for s in signals if s.indicator_name == indicator_name]

    @staticmethod
    def exclude_category(signals: List[Signal], category: str) -> List[Signal]:
        """
        Exclude signals of a category.

        Args:
            signals: List of signals.
            category: Category to exclude.

        Returns:
            Signals without that category.
        """
        return [s for s in signals if s.category != category]

    @staticmethod
    def recent(signals: List[Signal], max_age_seconds: int) -> List[Signal]:
        """
        Filter for recent signals.

        Args:
            signals: List of signals.
            max_age_seconds: Maximum age in seconds.

        Returns:
            Recent signals only.
        """
        cutoff = datetime.now() - pd.Timedelta(seconds=max_age_seconds)
        return [s for s in signals if s.timestamp >= cutoff]


# ============ SIGNAL SORTER ============


class SignalSorter:
    """
    Sorts signals by various criteria.
    """

    @staticmethod
    def by_confidence(signals: List[Signal], ascending: bool = False) -> List[Signal]:
        """
        Sort signals by confidence (highest first by default).

        Args:
            signals: List of signals.
            ascending: Sort ascending if True.

        Returns:
            Sorted list of signals.
        """
        return sorted(signals, key=lambda s: s.confidence, reverse=not ascending)

    @staticmethod
    def by_timestamp(signals: List[Signal], ascending: bool = False) -> List[Signal]:
        """
        Sort signals by timestamp (newest first by default).

        Args:
            signals: List of signals.
            ascending: Sort ascending if True.

        Returns:
            Sorted list of signals.
        """
        return sorted(signals, key=lambda s: s.timestamp, reverse=not ascending)

    @staticmethod
    def by_strength(signals: List[Signal]) -> List[Signal]:
        """
        Sort signals by strength (strong first).

        Args:
            signals: List of signals.

        Returns:
            Sorted list with strong signals first.
        """
        strength_order = {
            "EXTREME BULLISH": 0,
            "STRONG BULLISH": 1,
            "BULLISH": 2,
            "MODERATE": 3,
            "NEUTRAL": 4,
            "BEARISH": 5,
            "STRONG BEARISH": 6,
            "EXTREME BEARISH": 7,
        }

        return sorted(
            signals,
            key=lambda s: strength_order.get(s.strength, 99),
        )

    @staticmethod
    def by_category(signals: List[Signal]) -> Dict[str, List[Signal]]:
        """
        Group signals by category.

        Args:
            signals: List of signals.

        Returns:
            Dictionary mapping category to signals.
        """
        grouped: Dict[str, List[Signal]] = {}
        for signal in signals:
            if signal.category not in grouped:
                grouped[signal.category] = []
            grouped[signal.category].append(signal)
        return grouped