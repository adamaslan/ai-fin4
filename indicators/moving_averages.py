"""
Moving Average indicators (SMA, EMA).

Technical indicators for trend identification and smoothing price action.
"""

from typing import Set
import pandas as pd
from indicators.base import IndicatorBase, IndicatorMetadata, TrendIndicator
from logging_config import get_logger

logger = get_logger()


# ============ SIMPLE MOVING AVERAGE (SMA) ============


class SimpleMovingAverage(TrendIndicator):
    """
    Simple Moving Average (SMA) indicator.

    Calculates the arithmetic mean of price over N periods.
    Gives equal weight to all periods.

    Formula:
        SMA = (P1 + P2 + ... + Pn) / n

    Characteristics:
    - Slower to react to price changes
    - Less responsive to recent data
    - Good for identifying long-term trends
    - Useful as support/resistance levels
    """

    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.

        Args:
            period: Number of periods for moving average (default: 20).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get SMA metadata."""
        return IndicatorMetadata(
            name=f"Simple Moving Average ({self.period})",
            key=f"sma_{self.period}",
            min_bars_required=self.period,
            output_columns=(f"SMA_{self.period}",),
            category="trend",
            description=f"Arithmetic mean of Close price over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SMA.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with SMA column added.
        """
        result = df.copy()
        col_name = f"SMA_{self.period}"

        result[col_name] = result["Close"].rolling(
            window=self.period,
            min_periods=1,
        ).mean()

        return result


# ============ EXPONENTIAL MOVING AVERAGE (EMA) ============


class ExponentialMovingAverage(TrendIndicator):
    """
    Exponential Moving Average (EMA) indicator.

    Gives more weight to recent price data. More responsive than SMA
    but still smooth.

    Formula:
        EMA = Price * α + EMA_prev * (1 - α)
        where α = 2 / (period + 1)

    Characteristics:
    - More responsive to recent prices
    - Faster to react to price changes
    - Good for identifying short-term trends
    - Often used in MACD calculations
    - Less lag than SMA
    """

    def __init__(self, period: int = 20):
        """
        Initialize EMA indicator.

        Args:
            period: Number of periods for moving average (default: 20).

        Raises:
            ValueError: If period is not positive.
        """
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"Period must be positive integer, got {period}")

        self.period = period

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get EMA metadata."""
        return IndicatorMetadata(
            name=f"Exponential Moving Average ({self.period})",
            key=f"ema_{self.period}",
            min_bars_required=self.period,
            output_columns=(f"EMA_{self.period}",),
            category="trend",
            description=f"Weighted average emphasizing recent prices over {self.period} periods",
            parameters=(("period", int, self.period),),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EMA.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with EMA column added.
        """
        result = df.copy()
        col_name = f"EMA_{self.period}"

        result[col_name] = result["Close"].ewm(
            span=self.period,
            adjust=False,
        ).mean()

        return result


# ============ MOVING AVERAGE CROSSOVER SETUP ============


class MovingAverageCrossover(TrendIndicator):
    """
    Moving Average Crossover setup.

    Combines two MAs (fast and slow) for trend identification.
    Generates signals when fast MA crosses slow MA.

    Characteristics:
    - Fast MA above slow MA = uptrend
    - Fast MA below slow MA = downtrend
    - Crossovers indicate potential trend changes
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 20,
        ma_type: str = "ema",
    ):
        """
        Initialize MA Crossover indicator.

        Args:
            fast_period: Period for fast MA (default: 10).
            slow_period: Period for slow MA (default: 20).
            ma_type: Type of MA - 'sma' or 'ema' (default: 'ema').

        Raises:
            ValueError: If periods invalid or ma_type not recognized.
        """
        if not isinstance(fast_period, int) or fast_period <= 0:
            raise ValueError(f"fast_period must be positive, got {fast_period}")

        if not isinstance(slow_period, int) or slow_period <= 0:
            raise ValueError(f"slow_period must be positive, got {slow_period}")

        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be < slow_period ({slow_period})"
            )

        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got {ma_type}")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get MA Crossover metadata."""
        return IndicatorMetadata(
            name=f"MA Crossover ({self.ma_type.upper()} {self.fast_period}/{self.slow_period})",
            key=f"ma_cross_{self.fast_period}_{self.slow_period}",
            min_bars_required=self.slow_period,
            output_columns=(
                f"{self.ma_type.upper()}_{self.fast_period}",
                f"{self.ma_type.upper()}_{self.slow_period}",
                f"MA_Cross_Direction",
            ),
            category="trend",
            description=f"Crossover of {self.fast_period} and {self.slow_period} period {self.ma_type.upper()}",
            parameters=(
                ("fast_period", int, self.fast_period),
                ("slow_period", int, self.slow_period),
                ("ma_type", str, self.ma_type),
            ),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MA Crossover.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with both MAs and direction column.
        """
        result = df.copy()
        ma_prefix = self.ma_type.upper()
        fast_col = f"{ma_prefix}_{self.fast_period}"
        slow_col = f"{ma_prefix}_{self.slow_period}"
        direction_col = "MA_Cross_Direction"

        # Calculate both MAs
        if self.ma_type == "ema":
            result[fast_col] = result["Close"].ewm(
                span=self.fast_period, adjust=False
            ).mean()
            result[slow_col] = result["Close"].ewm(
                span=self.slow_period, adjust=False
            ).mean()
        else:  # sma
            result[fast_col] = result["Close"].rolling(self.fast_period).mean()
            result[slow_col] = result["Close"].rolling(self.slow_period).mean()

        # Calculate direction (1=fast above slow, -1=fast below slow, 0=equal)
        diff = result[fast_col] - result[slow_col]
        result[direction_col] = (
            (diff > 0).astype(int) - (diff < 0).astype(int)
        )

        return result


# ============ MOVING AVERAGE RIBBON ============


class MovingAverageRibbon(TrendIndicator):
    """
    Moving Average Ribbon.

    Multiple MAs of different periods displayed together.
    Creates a "ribbon" that shows trend strength and changes.

    Characteristics:
    - All MAs aligned = strong trend
    - MAs spread out = weak or transitional trend
    - MAs crossing = potential reversal
    """

    def __init__(
        self,
        periods: tuple = (10, 20, 50, 100, 200),
        ma_type: str = "ema",
    ):
        """
        Initialize MA Ribbon indicator.

        Args:
            periods: Tuple of periods for MAs (default: 10, 20, 50, 100, 200).
            ma_type: Type of MA - 'sma' or 'ema' (default: 'ema').

        Raises:
            ValueError: If parameters invalid.
        """
        if not periods or len(periods) < 2:
            raise ValueError("Must provide at least 2 periods")

        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("All periods must be positive integers")

        if len(periods) != len(set(periods)):
            raise ValueError("Periods must be unique")

        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got {ma_type}")

        self.periods = tuple(sorted(periods))
        self.ma_type = ma_type

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get MA Ribbon metadata."""
        output_cols = tuple(f"{self.ma_type.upper()}_{p}" for p in self.periods)

        return IndicatorMetadata(
            name=f"MA Ribbon ({self.ma_type.upper()} {len(self.periods)} MAs)",
            key=f"ma_ribbon_{self.ma_type}",
            min_bars_required=max(self.periods),
            output_columns=output_cols,
            category="trend",
            description=f"Multiple {self.ma_type.upper()} periods: {self.periods}",
            parameters=(
                ("periods", tuple, self.periods),
                ("ma_type", str, self.ma_type),
            ),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MA Ribbon.

        Args:
            df: Market data with Close column.

        Returns:
            DataFrame with all MAs added.
        """
        result = df.copy()
        ma_prefix = self.ma_type.upper()

        for period in self.periods:
            col_name = f"{ma_prefix}_{period}"

            if self.ma_type == "ema":
                result[col_name] = result["Close"].ewm(
                    span=period, adjust=False
                ).mean()
            else:  # sma
                result[col_name] = result["Close"].rolling(period).mean()

        return result