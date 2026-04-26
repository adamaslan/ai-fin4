"""
Signal sorting utilities.
"""

from __future__ import annotations

from typing import Dict, List

from signals.signal import Signal


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
