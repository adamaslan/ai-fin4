"""
Momentum indicators (RSI, MACD, Stochastic).

Technical indicators for measuring price momentum and overbought/oversold conditions.
"""

from typing import Set
import pandas as pd
import numpy as np
from indicators.base import IndicatorBase, IndicatorMetadata, MomentumIndicator
from logging_config import get_logger

logger = get_logger()


# ============ RELATIVE STRENGTH INDEX (RSI) ============


class RelativeStrengthIndex(MomentumIndicator):
    """
    Relative Strength Index (RSI) indicator.

    Measures the magnitude of recent price changes to evaluate
    overbought or oversold conditions.

    Formula:
        RS = Average Gain / Average Loss
        RSI = 100 - (100 / (1 + RS))

    Range: 0 to 100
    - RSI > 70 = Overbought (potential bearish reversal)
    - RSI < 30 = Oversold (potential bullish reversal)
    - RSI > 50 = Bullish bias
    - RSI < 50 = Bearish bias

    Characteristics:
    - Fast oscillator (no lag)
    - Useful for identifying reversals
    - Can stay overbought/oversold in strong trends
    """

    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.

        Args:
            period: Number of periods for RSI calculation (default: 14).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get RSI metadata."""
        return IndicatorMetadata(
            name=f"Relative Strength Index ({self.period})",
            key=f"rsi_{self.period}",
            min_bars_required=self.period + 1,
            output_columns=(f"RSI_{self.period}",),
            category="momentum",
            description=f"Momentum oscillator measuring overbought/oversold over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with RSI column added.
        """
        result = df.copy()
        col_name = f"RSI_{self.period}"

        # Calculate price changes
        delta = result["Close"].diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gain = gains.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = losses.rolling(window=self.period, min_periods=self.period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        result[col_name] = 100 - (100 / (1 + rs))

        return result


# ============ MACD (Moving Average Convergence Divergence) ============


class MACD(MomentumIndicator):
    """
    MACD (Moving Average Convergence Divergence) indicator.

    Combines two exponential moving averages to identify momentum
    changes and trends.

    Components:
    - MACD Line: 12-period EMA - 26-period EMA
    - Signal Line: 9-period EMA of MACD
    - Histogram: MACD Line - Signal Line

    Signals:
    - MACD crosses above Signal = Bullish
    - MACD crosses below Signal = Bearish
    - MACD crosses zero = Trend change
    - Histogram grows = Strengthening momentum
    - Histogram shrinks = Weakening momentum

    Characteristics:
    - Trend-following indicator
    - Lagging (but useful for confirmation)
    - Good for identifying entry/exit points
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        Initialize MACD indicator.

        Args:
            fast_period: Fast EMA period (default: 12).
            slow_period: Slow EMA period (default: 26).
            signal_period: Signal line EMA period (default: 9).

        Raises:
            ValueError: If parameters invalid.
        """
        if not isinstance(fast_period, int) or fast_period <= 0:
            raise ValueError(f"fast_period must be positive, got {fast_period}")

        if not isinstance(slow_period, int) or slow_period <= 0:
            raise ValueError(f"slow_period must be positive, got {slow_period}")

        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be < slow_period ({slow_period})"
            )

        if not isinstance(signal_period, int) or signal_period <= 0:
            raise ValueError(f"signal_period must be positive, got {signal_period}")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get MACD metadata."""
        return IndicatorMetadata(
            name=f"MACD ({self.fast_period},{self.slow_period},{self.signal_period})",
            key=f"macd_{self.fast_period}_{self.slow_period}",
            min_bars_required=self.slow_period,
            output_columns=("MACD", "MACD_Signal", "MACD_Histogram"),
            category="momentum",
            description=f"Momentum indicator using EMAs: {self.fast_period}-{self.slow_period}-{self.signal_period}",
            parameters=(
                ("fast_period", int, self.fast_period),
                ("slow_period", int, self.slow_period),
                ("signal_period", int, self.signal_period),
            ),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with MACD, Signal, and Histogram columns.
        """
        result = df.copy()

        # Calculate EMAs
        ema_fast = result["Close"].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = result["Close"].ewm(span=self.slow_period, adjust=False).mean()

        # MACD line
        result["MACD"] = ema_fast - ema_slow

        # Signal line (EMA of MACD)
        result["MACD_Signal"] = result["MACD"].ewm(
            span=self.signal_period, adjust=False
        ).mean()

        # Histogram
        result["MACD_Histogram"] = result["MACD"] - result["MACD_Signal"]

        return result


# ============ STOCHASTIC OSCILLATOR ============


class StochasticOscillator(MomentumIndicator):
    """
    Stochastic Oscillator indicator.

    Compares a particular closing price of a security to a range of
    its prices over time, to identify overbought/oversold conditions.

    Formula:
        %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = 3-period SMA of %K

    Range: 0 to 100
    - %K > 80 = Overbought
    - %K < 20 = Oversold
    - %K crosses %D = Signal

    Characteristics:
    - Fast oscillator (no lag)
    - Works best in ranging markets
    - Less effective in strong trends
    - Good for identifying reversals
    """

    def __init__(
        self,
        period: int = 14,
        smoothing_k: int = 3,
        smoothing_d: int = 3,
    ):
        """
        Initialize Stochastic Oscillator.

        Args:
            period: Period for High/Low lookback (default: 14).
            smoothing_k: Smoothing period for %K (default: 3).
            smoothing_d: Smoothing period for %D (default: 3).

        Raises:
            ValueError: If parameters invalid.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"period must be positive, got {period}")

        if not isinstance(smoothing_k, int) or smoothing_k <= 0:
            raise ValueError(f"smoothing_k must be positive, got {smoothing_k}")

        if not isinstance(smoothing_d, int) or smoothing_d <= 0:
            raise ValueError(f"smoothing_d must be positive, got {smoothing_d}")

        self.period = period
        self.smoothing_k = smoothing_k
        self.smoothing_d = smoothing_d

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get Stochastic metadata."""
        return IndicatorMetadata(
            name=f"Stochastic ({self.period},{self.smoothing_k},{self.smoothing_d})",
            key=f"stoch_{self.period}",
            min_bars_required=self.period,
            output_columns=("Stoch_K", "Stoch_D"),
            category="momentum",
            description=f"Overbought/oversold oscillator with {self.period}-period lookback",
            parameters=(
                ("period", int, self.period),
                ("smoothing_k", int, self.smoothing_k),
                ("smoothing_d", int, self.smoothing_d),
            ),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            df: Market data with High, Low, Close columns.

        Returns:
            DataFrame with Stoch_K and Stoch_D columns.
        """
        result = df.copy()

        # Highest high and lowest low
        high_n = result["High"].rolling(window=self.period).max()
        low_n = result["Low"].rolling(window=self.period).min()

        # Raw %K
        k_raw = 100 * ((result["Close"] - low_n) / (high_n - low_n))

        # Smooth %K
        result["Stoch_K"] = k_raw.rolling(window=self.smoothing_k).mean()

        # %D (SMA of %K)
        result["Stoch_D"] = result["Stoch_K"].rolling(window=self.smoothing_d).mean()

        return result