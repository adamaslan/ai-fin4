"""
Signal dataclass representing a detected trading signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any

from signals.signal_strength import SignalStrength
from type_defs import SignalInfo


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
