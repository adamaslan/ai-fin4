"""
Signal filtering utilities.
"""

from __future__ import annotations

from datetime import datetime
from typing import List
import pandas as pd

from signals.signal import Signal


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
