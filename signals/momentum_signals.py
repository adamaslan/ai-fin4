"""
Momentum signal detection.

Detects signals from RSI, MACD, and Stochastic indicators.
"""

from typing import List
import pandas as pd
import numpy as np
from signals.base import Signal, SignalDetector, SignalDetectorMetadata, SignalStrength
from logging_config import get_logger

logger = get_logger()


# ============ RSI SIGNAL DETECTOR ============


class RSISignalDetector(SignalDetector):
    """
    Detects Relative Strength Index (RSI) signals.

    Identifies overbought/oversold conditions and potential reversals.
    """

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        Initialize RSI detector.

        Args:
            period: RSI period.
            oversold: Oversold threshold (default: 30).
            overbought: Overbought threshold (default: 70).
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        return SignalDetectorMetadata(
            name=f"RSI ({self.period})",
            category="RSI",
            required_indicators=(f"RSI_{self.period}",),
            description=f"Detects overbought/oversold conditions",
            signal_categories=("RSI_OVERSOLD", "RSI_OVERBOUGHT"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect RSI signals.

        Args:
            df: Market data with RSI column.

        Returns:
            List of RSI signals.
        """
        signals = []

        if len(df) < 1:
            return signals

        current = df.iloc[-1]
        rsi_col = f"RSI_{self.period}"
        rsi = self._safe_float(current[rsi_col])

        if rsi is None:
            return signals

        # Oversold (bullish potential)
        if rsi < self.oversold:
            signals.append(
                Signal(
                    name=f"RSI OVERSOLD",
                    category="RSI",
                    strength=SignalStrength.BULLISH,
                    description=f"RSI({self.period}): {rsi:.1f} < {self.oversold} (Oversold)",
                    timeframe="unknown",
                    value=rsi,
                    confidence=0.65,
                    indicator_name="RSI",
                    trading_implication="Potential reversal zone; watch for support bounces",
                )
            )

        # Overbought (bearish potential)
        elif rsi > self.overbought:
            signals.append(
                Signal(
                    name=f"RSI OVERBOUGHT",
                    category="RSI",
                    strength=SignalStrength.BEARISH,
                    description=f"RSI({self.period}): {rsi:.1f} > {self.overbought} (Overbought)",
                    timeframe="unknown",
                    value=rsi,
                    confidence=0.65,
                    indicator_name="RSI",
                    trading_implication="Potential reversal or pullback; watch for resistance",
                )
            )

        # Neutral zone
        elif 40 <= rsi <= 60:
            if rsi > 55:
                strength = SignalStrength.MODERATE
                desc = f"RSI trending into overbought: {rsi:.1f}"
            elif rsi < 45:
                strength = SignalStrength.MODERATE
                desc = f"RSI trending into oversold: {rsi:.1f}"
            else:
                strength = SignalStrength.NEUTRAL
                desc = f"RSI in neutral zone: {rsi:.1f}"

            signals.append(
                Signal(
                    name="RSI NEUTRAL",
                    category="RSI",
                    strength=strength,
                    description=desc,
                    timeframe="unknown",
                    value=rsi,
                    confidence=0.5,
                    indicator_name="RSI",
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


# ============ MACD SIGNAL DETECTOR ============


class MACDSignalDetector(SignalDetector):
    """
    Detects MACD (Moving Average Convergence Divergence) signals.

    Identifies MACD line crossing signal line for trend changes.
    """

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        return SignalDetectorMetadata(
            name="MACD",
            category="MACD",
            required_indicators=("MACD", "MACD_Signal", "MACD_Histogram"),
            description="Detects MACD crossovers and momentum changes",
            signal_categories=("MACD_BULL_CROSS", "MACD_BEAR_CROSS"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect MACD signals.

        Args:
            df: Market data with MACD columns.

        Returns:
            List of MACD signals.
        """
        signals = []

        if len(df) < 2:
            return signals

        current = df.iloc[-1]
        previous = df.iloc[-2]

        macd_curr = self._safe_float(current["MACD"])
        signal_curr = self._safe_float(current["MACD_Signal"])
        macd_prev = self._safe_float(previous["MACD"])
        signal_prev = self._safe_float(previous["MACD_Signal"])
        histogram_curr = self._safe_float(current.get("MACD_Histogram"))

        if not all(v is not None for v in [macd_curr, signal_curr, macd_prev, signal_prev]):
            return signals

        # Bullish crossover
        if macd_prev <= signal_prev and macd_curr > signal_curr:
            signals.append(
                Signal(
                    name="MACD BULL CROSS",
                    category="MACD",
                    strength=SignalStrength.STRONG_BULLISH,
                    description="MACD crossed above signal line",
                    timeframe="unknown",
                    value=macd_curr,
                    confidence=0.8,
                    indicator_name="MACD",
                    details={"histogram": histogram_curr} if histogram_curr else {},
                    trading_implication="Strong buy signal; consider entering long positions",
                )
            )

        # Bearish crossover
        elif macd_prev >= signal_prev and macd_curr < signal_curr:
            signals.append(
                Signal(
                    name="MACD BEAR CROSS",
                    category="MACD",
                    strength=SignalStrength.STRONG_BEARISH,
                    description="MACD crossed below signal line",
                    timeframe="unknown",
                    value=macd_curr,
                    confidence=0.8,
                    indicator_name="MACD",
                    details={"histogram": histogram_curr} if histogram_curr else {},
                    trading_implication="Strong sell signal; consider exiting longs or entering shorts",
                )
            )

        # MACD zero crossing (additional signal)
        if macd_prev < 0 and macd_curr > 0:
            signals.append(
                Signal(
                    name="MACD ZERO CROSS UP",
                    category="MACD",
                    strength=SignalStrength.MODERATE,
                    description="MACD crossed above zero",
                    timeframe="unknown",
                    value=macd_curr,
                    confidence=0.7,
                    indicator_name="MACD",
                    trading_implication="Momentum turning positive",
                )
            )

        elif macd_prev > 0 and macd_curr < 0:
            signals.append(
                Signal(
                    name="MACD ZERO CROSS DOWN",
                    category="MACD",
                    strength=SignalStrength.MODERATE,
                    description="MACD crossed below zero",
                    timeframe="unknown",
                    value=macd_curr,
                    confidence=0.7,
                    indicator_name="MACD",
                    trading_implication="Momentum turning negative",
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


# ============ STOCHASTIC SIGNAL DETECTOR ============


class StochasticSignalDetector(SignalDetector):
    """
    Detects Stochastic Oscillator signals.

    Identifies overbought/oversold and crossover conditions.
    """

    def __init__(self, period: int = 14, oversold: int = 20, overbought: int = 80):
        """
        Initialize Stochastic detector.

        Args:
            period: Stochastic period.
            oversold: Oversold threshold (default: 20).
            overbought: Overbought threshold (default: 80).
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        return SignalDetectorMetadata(
            name=f"Stochastic ({self.period})",
            category="STOCHASTIC",
            required_indicators=("Stoch_K", "Stoch_D"),
            description="Detects Stochastic overbought/oversold and crossovers",
            signal_categories=("STOCH_OVERSOLD", "STOCH_OVERBOUGHT", "STOCH_CROSS"),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect Stochastic signals.

        Args:
            df: Market data with Stochastic columns.

        Returns:
            List of Stochastic signals.
        """
        signals = []

        if len(df) < 2:
            return signals

        current = df.iloc[-1]
        k_curr = self._safe_float(current.get("Stoch_K"))
        d_curr = self._safe_float(current.get("Stoch_D"))

        if k_curr is None or d_curr is None:
            return signals

        # Oversold
        if k_curr < self.oversold:
            signals.append(
                Signal(
                    name="STOCHASTIC OVERSOLD",
                    category="STOCHASTIC",
                    strength=SignalStrength.BULLISH,
                    description=f"Stochastic %K: {k_curr:.1f} < {self.oversold} (Oversold)",
                    timeframe="unknown",
                    value=k_curr,
                    confidence=0.65,
                    indicator_name="Stochastic",
                    trading_implication="Oversold condition; potential reversal",
                )
            )

        # Overbought
        elif k_curr > self.overbought:
            signals.append(
                Signal(
                    name="STOCHASTIC OVERBOUGHT",
                    category="STOCHASTIC",
                    strength=SignalStrength.BEARISH,
                    description=f"Stochastic %K: {k_curr:.1f} > {self.overbought} (Overbought)",
                    timeframe="unknown",
                    value=k_curr,
                    confidence=0.65,
                    indicator_name="Stochastic",
                    trading_implication="Overbought condition; potential reversal",
                )
            )

        # %K/%D crossover
        if len(df) >= 2:
            previous = df.iloc[-2]
            k_prev = self._safe_float(previous.get("Stoch_K"))
            d_prev = self._safe_float(previous.get("Stoch_D"))

            if k_prev is not None and d_prev is not None:
                if k_prev <= d_prev and k_curr > d_curr:
                    signals.append(
                        Signal(
                            name="STOCHASTIC %K CROSS ABOVE %D",
                            category="STOCHASTIC",
                            strength=SignalStrength.BULLISH,
                            description="%K crossed above %D",
                            timeframe="unknown",
                            value=k_curr,
                            confidence=0.7,
                            indicator_name="Stochastic",
                            trading_implication="Bullish momentum; consider long entry",
                        )
                    )

                elif k_prev >= d_prev and k_curr < d_curr:
                    signals.append(
                        Signal(
                            name="STOCHASTIC %K CROSS BELOW %D",
                            category="STOCHASTIC",
                            strength=SignalStrength.BEARISH,
                            description="%K crossed below %D",
                            timeframe="unknown",
                            value=k_curr,
                            confidence=0.7,
                            indicator_name="Stochastic",
                            trading_implication="Bearish momentum; consider short entry",
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