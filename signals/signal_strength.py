"""
Signal strength constants and utilities.
"""

from __future__ import annotations

from typing import Set


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
