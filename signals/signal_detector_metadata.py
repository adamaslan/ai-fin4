"""
Signal detector metadata dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass


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
