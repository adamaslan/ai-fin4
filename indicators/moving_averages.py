"""
Moving Average signal detection.

Detects signals from moving average crossovers and positioning.
"""

from typing import List
import pandas as pd
import numpy as np
from signals.base import Signal, SignalDetector, SignalDetectorMetadata, SignalStrength
from logging_config import get_logger

logger = get_logger()


# ============ MA CROSSOVER DETECTOR ============


class MovingAverageCrossoverDetector(SignalDetector):
    """
    Detects moving average crossover signals.

    Identifies when a fast MA crosses above/below a slow MA,
    indicating potential trend changes.
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        """
        Initialize MA Crossover detector.

        Args:
            fast_period: Fast MA period.
            slow_period: Slow MA period.
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        return SignalDetectorMetadata(
            name=f"MA Crossover ({self.fast_period}/{self.slow_period})",
            category="MA_CROSS",
            required_indicators=(f"SMA_{self.fast_period}", f"SMA_{self.slow_period}"),
            description=f"Detects {self.fast_period} MA crossing {self.slow_period} MA",
            signal_categories=("MA_BULL_CROSS", "MA_BEAR_CROSS"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect MA crossover signals.

        Args:
            df: Market data with both MA columns.

        Returns:
            List of crossover signals.
        """
        signals = []

        fast_col = f"SMA_{self.fast_period}"
        slow_col = f"SMA_{self.slow_period}"

        # Need at least 2 bars to detect crossover
        if len(df) < 2:
            return signals

        current = df.iloc[-1]
        previous = df.iloc[-2]

        fast_curr = self._safe_float(current[fast_col])
        slow_curr = self._safe_float(current[slow_col])
        fast_prev = self._safe_float(previous[fast_col])
        slow_prev = self._safe_float(previous[slow_col])

        # Bullish crossover: fast crosses above slow
        if all(v is not None for v in [fast_curr, slow_curr, fast_prev, slow_prev]):
            if fast_prev <= slow_prev and fast_curr > slow_curr:
                signals.append(
                    Signal(
                        name=f"{self.fast_period}/{self.slow_period} MA BULL CROSS",
                        category="MA_CROSS",
                        strength=SignalStrength.BULLISH,
                        description=f"{self.fast_period} MA crossed above {self.slow_period} MA",
                        timeframe="unknown",
                        value=fast_curr,
                        confidence=0.7,
                        indicator_name="SMA",
                        trading_implication="Uptrend forming; consider long entries",
                    )
                )

            # Bearish crossover: fast crosses below slow
            elif fast_prev >= slow_prev and fast_curr < slow_curr:
                signals.append(
                    Signal(
                        name=f"{self.fast_period}/{self.slow_period} MA BEAR CROSS",
                        category="MA_CROSS",
                        strength=SignalStrength.BEARISH,
                        description=f"{self.fast_period} MA crossed below {self.slow_period} MA",
                        timeframe="unknown",
                        value=fast_curr,
                        confidence=0.7,
                        indicator_name="SMA",
                        trading_implication="Downtrend forming; consider short entries or exits",
                    )
                )

        return signals

    @staticmethod
    def _safe_float(value) -> float:
        """Safely convert to float, return None for invalid."""
        try:
            if pd.isna(value) or np.isinf(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None


# ============ MA POSITIONING DETECTOR ============


class MovingAveragePositioningDetector(SignalDetector):
    """
    Detects signals from price positioning relative to MAs.

    Identifies when price is above/below key moving averages.
    """

    def __init__(self, periods: tuple = (20, 50, 200)):
        """
        Initialize MA Positioning detector.

        Args:
            periods: Tuple of MA periods to check.
        """
        self.periods = tuple(sorted(periods))

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        required = tuple(f"SMA_{p}" for p in self.periods)
        return SignalDetectorMetadata(
            name=f"MA Positioning ({self.periods})",
            category="MA_POSITION",
            required_indicators=required,
            description=f"Detects price positioning relative to {self.periods} MAs",
            signal_categories=("MA_ABOVE", "MA_BELOW", "MA_ALIGNED"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect MA positioning signals.

        Args:
            df: Market data with MA columns.

        Returns:
            List of positioning signals.
        """
        signals = []

        if len(df) < 1:
            return signals

        current = df.iloc[-1]
        close = self._safe_float(current["Close"])

        if close is None:
            return signals

        # Get all MA values
        mas = {}
        for period in self.periods:
            col = f"SMA_{period}"
            value = self._safe_float(current[col])
            if value is not None:
                mas[period] = value

        if not mas:
            return signals

        # Check price above all MAs (bullish alignment)
        if all(close > ma for ma in mas.values()):
            signals.append(
                Signal(
                    name="PRICE ABOVE ALL MAs",
                    category="MA_POSITION",
                    strength=SignalStrength.BULLISH,
                    description=f"Price is above all moving averages: {self.periods}",
                    timeframe="unknown",
                    value=close,
                    confidence=0.8,
                    indicator_name="SMA",
                    trading_implication="Strong uptrend; favor long positions",
                )
            )

        # Check price below all MAs (bearish alignment)
        elif all(close < ma for ma in mas.values()):
            signals.append(
                Signal(
                    name="PRICE BELOW ALL MAs",
                    category="MA_POSITION",
                    strength=SignalStrength.BEARISH,
                    description=f"Price is below all moving averages: {self.periods}",
                    timeframe="unknown",
                    value=close,
                    confidence=0.8,
                    indicator_name="SMA",
                    trading_implication="Strong downtrend; favor short positions",
                )
            )

        return signals

    @staticmethod
    def _safe_float(value) -> float:
        """Safely convert to float, return None for invalid."""
        try:
            if pd.isna(value) or np.isinf(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None


# ============ MA RIBBON DETECTOR ============


class MovingAverageRibbonDetector(SignalDetector):
    """
    Detects signals from MA ribbon alignment.

    When multiple MAs are aligned/stacked, indicates strong trend.
    When spread out, indicates weak or changing trend.
    """

    def __init__(self, periods: tuple = (10, 20, 50, 100, 200)):
        """
        Initialize MA Ribbon detector.

        Args:
            periods: Tuple of MA periods in ribbon.
        """
        self.periods = tuple(sorted(periods))

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        required = tuple(f"SMA_{p}" for p in self.periods)
        return SignalDetectorMetadata(
            name=f"MA Ribbon ({len(self.periods)} MAs)",
            category="MA_RIBBON",
            required_indicators=required,
            description="Detects MA ribbon alignment and trend strength",
            signal_categories=("RIBBON_ALIGNED", "RIBBON_SPREAD"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect MA ribbon signals.

        Args:
            df: Market data with MA columns.

        Returns:
            List of ribbon signals.
        """
        signals = []

        if len(df) < 1:
            return signals

        current = df.iloc[-1]

        # Get all MA values
        mas = []
        for period in self.periods:
            col = f"SMA_{period}"
            value = self._safe_float(current[col])
            if value is not None:
                mas.append(value)

        if len(mas) < 2:
            return signals

        mas_sorted = sorted(mas)
        total_range = mas_sorted[-1] - mas_sorted[0]
        close = self._safe_float(current["Close"])

        if close is None or total_range == 0:
            return signals

        # Calculate alignment (compression = aligned, expansion = spread)
        spread_ratio = total_range / close

        # Ribbon aligned (strong trend) = low spread
        if spread_ratio < 0.02:  # Less than 2% spread
            # Determine direction
            avg_ma = sum(mas) / len(mas)
            if close > avg_ma:
                strength = SignalStrength.STRONG_BULLISH
                implication = "Ribbon compressed upward; strong uptrend"
            else:
                strength = SignalStrength.STRONG_BEARISH
                implication = "Ribbon compressed downward; strong downtrend"

            signals.append(
                Signal(
                    name="MA RIBBON ALIGNED",
                    category="MA_RIBBON",
                    strength=strength,
                    description=f"All {len(self.periods)} MAs are tightly aligned",
                    timeframe="unknown",
                    value=spread_ratio,
                    confidence=0.85,
                    indicator_name="SMA",
                    trading_implication=implication,
                )
            )

        # Ribbon spread (weak trend or transition)
        elif spread_ratio > 0.05:  # More than 5% spread
            signals.append(
                Signal(
                    name="MA RIBBON SPREAD",
                    category="MA_RIBBON",
                    strength=SignalStrength.NEUTRAL,
                    description=f"MAs are spread apart (weak trend or transition)",
                    timeframe="unknown",
                    value=spread_ratio,
                    confidence=0.6,
                    indicator_name="SMA",
                    trading_implication="Weak trend or consolidation; wait for ribbon compression",
                )
            )

        return signals

    @staticmethod
    def _safe_float(value) -> float:
        """Safely convert to float, return None for invalid."""
        try:
            if pd.isna(value) or np.isinf(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None