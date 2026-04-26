"""
Base classes for technical indicators.

Provides abstract base classes and interfaces for implementing
technical indicators with a consistent API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import pandas as pd
import numpy as np
from logging_config import get_logger
from exceptions import InsufficientDataError, SignalDetectionError
from type_defs import IndicatorData

logger = get_logger()


# ============ INDICATOR METADATA ============


@dataclass(frozen=True)
class IndicatorMetadata:
    """
    Metadata about an indicator.

    Provides information about an indicator's requirements, capabilities,
    and output columns.
    """

    name: str
    """Human-readable indicator name (e.g., 'Moving Average')."""

    key: str
    """Unique key for the indicator (e.g., 'sma', 'rsi')."""

    min_bars_required: int
    """Minimum bars needed for calculation."""

    output_columns: tuple
    """Names of columns added to DataFrame by this indicator."""

    category: str
    """Indicator category (trend, momentum, volatility, volume)."""

    description: str
    """Description of what the indicator does."""

    parameters: tuple
    """Tuples of (param_name, param_type, default_value)."""

    def requires_columns(self) -> Set[str]:
        """
        Get required columns from market data.

        Returns:
            Set of column names required (e.g., {'Close', 'Volume'}).
        """
        return {"Open", "High", "Low", "Close", "Volume"}

    def __str__(self) -> str:
        """Return formatted metadata string."""
        return f"{self.name} ({self.key})"


# ============ INDICATOR BASE CLASS ============


class IndicatorBase(ABC):
    """
    Abstract base class for all technical indicators.

    Provides common interface for calculating indicators on market data.
    All concrete indicators must inherit from this class and implement
    the `calculate()` method.

    Example:
        >>> class SimpleMovingAverage(IndicatorBase):
        ...     def __init__(self, period: int):
        ...         self.period = period
        ...
        ...     @property
        ...     def metadata(self) -> IndicatorMetadata:
        ...         return IndicatorMetadata(
        ...             name="Simple Moving Average",
        ...             key="sma",
        ...             min_bars_required=self.period,
        ...             output_columns=("SMA",),
        ...             category="trend",
        ...             description="Average price over N periods",
        ...             parameters=(("period", int, 20),),
        ...         )
        ...
        ...     def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        ...         df = df.copy()
        ...         df["SMA"] = df["Close"].rolling(self.period).mean()
        ...         return df
    """

    @property
    @abstractmethod
    def metadata(self) -> IndicatorMetadata:
        """
        Get metadata about this indicator.

        Must be implemented by subclasses.

        Returns:
            IndicatorMetadata with indicator information.
        """
        pass

    def validate(self, df: pd.DataFrame) -> None:
        """
        Validate that input data meets requirements.

        Checks:
        - DataFrame is not empty
        - Has required columns
        - Has sufficient bars

        Args:
            df: Market data to validate.

        Raises:
            InsufficientDataError: If data doesn't meet requirements.
            SignalDetectionError: If data structure is invalid.
        """
        meta = self.metadata

        # Check empty
        if df.empty:
            raise SignalDetectionError(
                f"Cannot calculate {meta.name}: data is empty",
                indicator=meta.key,
            )

        # Check required columns
        required = meta.requires_columns()
        missing = required - set(df.columns)

        if missing:
            raise SignalDetectionError(
                f"Cannot calculate {meta.name}: missing columns {missing}",
                indicator=meta.key,
            )

        # Check sufficient bars
        if len(df) < meta.min_bars_required:
            raise InsufficientDataError(
                f"Insufficient data for {meta.name}",
                required=meta.min_bars_required,
                actual=len(df),
                indicator=meta.key,
            )

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values and add to DataFrame.

        Must be implemented by subclasses. Should:
        1. Create a copy of the DataFrame
        2. Calculate indicator values
        3. Add to DataFrame as new columns
        4. Return modified DataFrame

        Args:
            df: Market data with at least OHLCV columns.

        Returns:
            DataFrame with indicator columns added.

        Raises:
            InsufficientDataError: If not enough data.
            SignalDetectionError: If calculation fails.
        """
        pass

    def execute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute indicator calculation with validation.

        Public method that validates input, executes calculation,
        and handles errors. Preferred over direct `calculate()` call.

        Args:
            df: Market data DataFrame.

        Returns:
            DataFrame with indicator added.

        Raises:
            InsufficientDataError: If insufficient data.
            SignalDetectionError: If calculation fails.

        Example:
            >>> sma = SimpleMovingAverage(period=20)
            >>> result = sma.execute(market_data)
        """
        meta = self.metadata

        try:
            # Validate input
            self.validate(df)

            # Calculate
            logger.debug(f"Calculating {meta.name} on {len(df)} bars")
            result = self.calculate(df)

            # Verify output
            for col in meta.output_columns:
                if col not in result.columns:
                    raise SignalDetectionError(
                        f"{meta.name} failed to create column: {col}",
                        indicator=meta.key,
                    )

            logger.debug(f"✓ {meta.name} calculated successfully")
            return result

        except (InsufficientDataError, SignalDetectionError):
            raise
        except Exception as e:
            raise SignalDetectionError(
                f"Error calculating {meta.name}: {str(e)}",
                indicator=meta.key,
                exception=e,
            ) from e

    def __str__(self) -> str:
        """Return string representation of indicator."""
        return str(self.metadata)

    def __repr__(self) -> str:
        """Return detailed representation of indicator."""
        meta = self.metadata
        return f"{meta.key}({meta.description})"


# ============ CATEGORY-SPECIFIC BASE CLASSES ============


class TrendIndicator(IndicatorBase):
    """
    Base class for trend indicators (MA, ADX, etc.).

    Trend indicators identify the direction of price movement.
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Implement metadata with category='trend'."""
        raise NotImplementedError("Subclass must implement metadata property")

    def get_category(self) -> str:
        """Get indicator category."""
        return "trend"


class MomentumIndicator(IndicatorBase):
    """
    Base class for momentum indicators (RSI, MACD, Stochastic, etc.).

    Momentum indicators measure the rate of change and strength of price movements.
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Implement metadata with category='momentum'."""
        raise NotImplementedError("Subclass must implement metadata property")

    def get_category(self) -> str:
        """Get indicator category."""
        return "momentum"


class VolatilityIndicator(IndicatorBase):
    """
    Base class for volatility indicators (Bollinger Bands, ATR, etc.).

    Volatility indicators measure price dispersion and variability.
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Implement metadata with category='volatility'."""
        raise NotImplementedError("Subclass must implement metadata property")

    def get_category(self) -> str:
        """Get indicator category."""
        return "volatility"


class VolumeIndicator(IndicatorBase):
    """
    Base class for volume indicators (OBV, Volume MA, etc.).

    Volume indicators analyze trading volume patterns.
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Implement metadata with category='volume'."""
        raise NotImplementedError("Subclass must implement metadata property")

    def requires_columns(self) -> Set[str]:
        """Volume indicators need Volume column."""
        return {"Close", "Volume"}

    def get_category(self) -> str:
        """Get indicator category."""
        return "volume"


# ============ COMPOSITE INDICATOR ============


class CompositeIndicator(IndicatorBase):
    """
    Indicator composed of multiple sub-indicators.

    Allows combining multiple indicators into a single calculation.
    Useful for complex indicators that depend on other indicators.

    Example:
        >>> sma_fast = SimpleMovingAverage(10)
        >>> sma_slow = SimpleMovingAverage(20)
        >>> composite = CompositeIndicator(
        ...     name="MA Crossover Setup",
        ...     indicators=[sma_fast, sma_slow]
        ... )
    """

    def __init__(
        self,
        name: str,
        key: str,
        indicators: List[IndicatorBase],
        category: str = "composite",
    ):
        """
        Initialize composite indicator.

        Args:
            name: Human-readable name.
            key: Unique identifier key.
            indicators: List of sub-indicators to execute.
            category: Indicator category (default: composite).
        """
        self.name = name
        self.key = key
        self.indicators = indicators
        self.category = category

    @property
    def metadata(self) -> IndicatorMetadata:
        """Get composite indicator metadata."""
        # Aggregate output columns from all sub-indicators
        output_cols = []
        for ind in self.indicators:
            output_cols.extend(ind.metadata.output_columns)

        # Max bars required from all sub-indicators
        min_bars = max(
            (ind.metadata.min_bars_required for ind in self.indicators),
            default=50,
        )

        return IndicatorMetadata(
            name=self.name,
            key=self.key,
            min_bars_required=min_bars,
            output_columns=tuple(output_cols),
            category=self.category,
            description=f"Composite of {len(self.indicators)} indicators",
            parameters=(),
        )

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute all sub-indicators in sequence.

        Args:
            df: Market data.

        Returns:
            DataFrame with all indicators calculated.
        """
        result = df.copy()

        for indicator in self.indicators:
            logger.debug(f"Calculating sub-indicator: {indicator.metadata.name}")
            result = indicator.execute(result)

        return result


# ============ INDICATOR GROUP ============


class IndicatorGroup:
    """
    Groups multiple indicators together.

    Useful for managing indicators of the same category or
    indicators that work together.

    Example:
        >>> momentum_group = IndicatorGroup(
        ...     name="Momentum Suite",
        ...     indicators=[rsi, macd, stochastic]
        ... )
        >>> result = momentum_group.execute(data)
    """

    def __init__(
        self,
        name: str,
        indicators: List[IndicatorBase],
    ):
        """
        Initialize indicator group.

        Args:
            name: Group name.
            indicators: List of indicators in group.
        """
        self.name = name
        self.indicators = indicators

    def execute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute all indicators in the group.

        Args:
            df: Market data.

        Returns:
            DataFrame with all indicators calculated.
        """
        result = df.copy()

        logger.info(f"Executing indicator group: {self.name} ({len(self.indicators)} indicators)")

        for indicator in self.indicators:
            try:
                result = indicator.execute(result)
            except (InsufficientDataError, SignalDetectionError) as e:
                logger.warning(f"Skipping {indicator.metadata.name}: {str(e)}")
                continue

        return result

    def get_output_columns(self) -> List[str]:
        """
        Get all output columns from group indicators.

        Returns:
            List of column names added by group.
        """
        columns = []
        for indicator in self.indicators:
            columns.extend(indicator.metadata.output_columns)
        return columns

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({len(self.indicators)} indicators)"

    def __repr__(self) -> str:
        """Return detailed representation."""
        indicator_names = [ind.metadata.name for ind in self.indicators]
        return f"IndicatorGroup({self.name}, {indicator_names})"