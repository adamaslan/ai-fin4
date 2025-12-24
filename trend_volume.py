"""
Trend and Volume indicators (ADX, ATR, OBV, Volume MA).

Technical indicators for trend strength and volume analysis.
"""

from typing import Set
import pandas as pd
import numpy as np
from indicators.base import (
    IndicatorBase,
    IndicatorMetadata,
    TrendIndicator,
    VolumeIndicator,
)
from logging_config import get_logger

logger = get_logger()


# ============ AVERAGE TRUE RANGE (ATR) ============


class AverageTrueRange(TrendIndicator):
    """
    Average True Range (ATR) indicator.

    Measures market volatility by analyzing the range of price movement
    per period. High ATR = high volatility, Low ATR = low volatility.

    Formula:
        TR = Max(High - Low, |High - Close_prev|, |Low - Close_prev|)
        ATR = SMA of TR over N periods

    Uses:
    - Position sizing (wider stops in high ATR)
    - Volatility confirmation
    - Entry/exit levels
    - Stop loss placement

    Characteristics:
    - Non-directional (measures volatility only)
    - Useful with other indicators
    - Adapts to market conditions
    """

    def __init__(self, period: int = 14):
        """
        Initialize ATR indicator.

        Args:
            period: Number of periods for ATR calculation (default: 14).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get ATR metadata."""
        return IndicatorMetadata(
            name=f"Average True Range ({self.period})",
            key=f"atr_{self.period}",
            min_bars_required=self.period + 1,
            output_columns=(f"ATR_{self.period}", f"TR_{self.period}"),
            category="trend",
            description=f"Volatility measure over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ATR.

        Args:
            df: Market data with High, Low, Close columns.

        Returns:
            DataFrame with ATR and TR columns.
        """
        result = df.copy()

        # Calculate True Range
        high_low = result["High"] - result["Low"]
        high_close = np.abs(result["High"] - result["Close"].shift())
        low_close = np.abs(result["Low"] - result["Close"].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)

        result[f"TR_{self.period}"] = true_range

        # Calculate ATR (SMA of TR)
        result[f"ATR_{self.period}"] = true_range.rolling(self.period).mean()

        return result


# ============ AVERAGE DIRECTIONAL INDEX (ADX) ============


class AverageDirectionalIndex(TrendIndicator):
    """
    Average Directional Index (ADX) indicator.

    Measures trend strength on a scale of 0-100. Doesn't indicate
    direction, only strength.

    Components:
    - +DI (Plus Directional Indicator)
    - -DI (Minus Directional Indicator)
    - ADX (Average of DI difference)

    Interpretation:
    - ADX < 20 = No trend (directionless market)
    - ADX 20-40 = Weak to moderate trend
    - ADX 40-60 = Strong trend
    - ADX > 60 = Very strong trend
    - +DI > -DI = Uptrend direction
    - -DI > +DI = Downtrend direction

    Characteristics:
    - Trend strength confirmation
    - Helps avoid ranging markets
    - Lagging indicator
    - Works well with trending systems
    """

    def __init__(self, period: int = 14):
        """
        Initialize ADX indicator.

        Args:
            period: Number of periods for ADX calculation (default: 14).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get ADX metadata."""
        return IndicatorMetadata(
            name=f"Average Directional Index ({self.period})",
            key=f"adx_{self.period}",
            min_bars_required=self.period * 2,
            output_columns=(f"ADX_{self.period}", f"Plus_DI_{self.period}", f"Minus_DI_{self.period}"),
            category="trend",
            description=f"Trend strength indicator over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ADX with +DI and -DI.

        Args:
            df: Market data with High, Low, Close columns.

        Returns:
            DataFrame with ADX, Plus_DI, and Minus_DI columns.
        """
        result = df.copy()

        # Calculate True Range
        high_low = result["High"] - result["Low"]
        high_close = np.abs(result["High"] - result["Close"].shift())
        low_close = np.abs(result["Low"] - result["Close"].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        tr = np.max(ranges, axis=1)

        # Calculate Directional Movements
        plus_dm = result["High"].diff()
        minus_dm = -result["Low"].diff()

        # Apply directional rules
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Prevent both being positive
        both_positive = (plus_dm > 0) & (minus_dm > 0)
        plus_dm[both_positive & (plus_dm < minus_dm)] = 0
        minus_dm[both_positive & (minus_dm < plus_dm)] = 0

        # Calculate DI
        tr_sum = tr.rolling(self.period).sum()
        plus_di = 100 * (plus_dm.rolling(self.period).sum() / tr_sum)
        minus_di = 100 * (minus_dm.rolling(self.period).sum() / tr_sum)

        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(self.period).mean()

        result[f"Plus_DI_{self.period}"] = plus_di
        result[f"Minus_DI_{self.period}"] = minus_di
        result[f"ADX_{self.period}"] = adx

        return result


# ============ ON-BALANCE VOLUME (OBV) ============


class OnBalanceVolume(VolumeIndicator):
    """
    On-Balance Volume (OBV) indicator.

    Accumulates volume on up days and subtracts volume on down days
    to measure buying and selling pressure.

    Formula:
        OBV = Previous OBV + Volume (if Close > Previous Close)
        OBV = Previous OBV - Volume (if Close < Previous Close)
        OBV = Previous OBV (if Close = Previous Close)

    Interpretation:
    - Rising OBV = Buying pressure increasing
    - Falling OBV = Selling pressure increasing
    - OBV divergences = Potential reversals

    Uses:
    - Confirm trends (OBV should trend with price)
    - Spot divergences (price up, OBV down = weakness)
    - Volume confirmation

    Characteristics:
    - Volume-weighted indicator
    - Cumulative (depends on starting point)
    - Good for confirmation
    - Works best with trends
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get OBV metadata."""
        return IndicatorMetadata(
            name="On-Balance Volume",
            key="obv",
            min_bars_required=1,
            output_columns=("OBV",),
            category="volume",
            description="Cumulative volume based on price direction",
            parameters=(),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate OBV.

        Args:
            df: Market data with Close and Volume columns.

        Returns:
            DataFrame with OBV column.
        """
        result = df.copy()

        # Determine if close is up, down, or same
        obv = pd.Series(0.0, index=df.index)

        for i in range(1, len(result)):
            if result["Close"].iloc[i] > result["Close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + result["Volume"].iloc[i]
            elif result["Close"].iloc[i] < result["Close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - result["Volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        result["OBV"] = obv
        return result


# ============ VOLUME MOVING AVERAGE ============


class VolumeMovingAverage(VolumeIndicator):
    """
    Volume Moving Average indicator.

    Smooths volume data using simple moving average. Helps identify
    volume trends and spikes relative to baseline.

    Uses:
    - Volume confirmation (high volume on breakouts)
    - Identify volume spikes
    - Trend analysis (volume with trend is healthy)
    - Detect divergences

    Characteristics:
    - Simple indicator
    - Good baseline for comparison
    - Works with any timeframe
    - Often used with volume threshold filters
    """

    def __init__(self, period: int = 20):
        """
        Initialize Volume MA indicator.

        Args:
            period: Number of periods for MA (default: 20).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get Volume MA metadata."""
        return IndicatorMetadata(
            name=f"Volume Moving Average ({self.period})",
            key=f"vol_ma_{self.period}",
            min_bars_required=self.period,
            output_columns=(f"Volume_MA_{self.period}",),
            category="volume",
            description=f"Simple moving average of volume over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Volume MA.

        Args:
            df: Market data with Volume column.

        Returns:
            DataFrame with Volume_MA column.
        """
        result = df.copy()
        col_name = f"Volume_MA_{self.period}"

        result[col_name] = result["Volume"].rolling(
            window=self.period,
            min_periods=1,
        ).mean()

        return result