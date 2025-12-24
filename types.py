"""
Type hints and custom type aliases for the signal analyzer.

Centralizes type definitions for consistency and clarity throughout
the codebase. Enables better IDE autocomplete and type checking.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    Union,
)
from datetime import datetime
import pandas as pd
import numpy as np


# ============ BASIC TYPE ALIASES ============

# Numbers
PriceValue = Union[int, float]
"""A price or price-related value (can be int or float)."""

PercentValue = float
"""A percentage value (0.0 to 100.0 or 0.0 to 1.0 depending on context)."""

VolumeValue = int
"""A volume value (number of shares traded)."""

BarCount = int
"""A count of price bars/candles."""

# Strings
Symbol = str
"""Stock ticker symbol (e.g., 'AAPL', 'SPY')."""

Timeframe = str
"""Timeframe/interval identifier (e.g., '1m', '5m', '1h', '1d')."""

Period = str
"""Data period string for yfinance (e.g., '1d', '60d', 'max')."""


# ============ DATA STRUCTURE ALIASES ============

# DataFrames
MarketData = pd.DataFrame
"""DataFrame containing OHLCV data (Open, High, Low, Close, Volume)."""

IndicatorData = pd.DataFrame
"""DataFrame with calculated indicators added as columns."""

# Dictionary types
ConfigDict = Dict[str, Any]
"""Configuration dictionary (flexible structure)."""

SignalDict = Dict[str, Any]
"""Signal detection result as dictionary."""

MetadataDict = Dict[str, Any]
"""Metadata dictionary (context information)."""

DetailsDict = Dict[str, str]
"""Details/context dictionary for error messages."""


# ============ SIGNAL-RELATED TYPES ============

class SignalInfo(TypedDict, total=False):
    """
    Typed dictionary for signal information.

    Represents a detected signal with all contextual information.
    """

    signal: str
    """Signal name/identifier."""

    description: str
    """Human-readable description of the signal."""

    strength: str
    """Signal strength (BULLISH, BEARISH, NEUTRAL, etc.)."""

    category: str
    """Signal category (MA_CROSS, RSI, MACD, etc.)."""

    timeframe: str
    """Timeframe on which signal was detected."""

    value: float
    """Numeric value associated with signal."""

    distance_pct: Optional[float]
    """Distance from level in percentage."""

    volume_ratio: Optional[float]
    """Volume ratio if applicable."""

    stoch_k: Optional[float]
    """Stochastic %K value if applicable."""

    trading_implication: Optional[str]
    """Suggested trading action based on signal."""


class AnalysisResult(TypedDict, total=False):
    """
    Typed dictionary for analysis results.

    Contains complete analysis output with metadata, signals, and data.
    """

    symbol: str
    """Stock symbol analyzed."""

    interval: str
    """Timeframe analyzed."""

    timestamp: str
    """Timestamp of analysis."""

    bars: int
    """Number of bars analyzed."""

    signals: List[SignalInfo]
    """List of detected signals."""

    signal_summary: Dict[str, Any]
    """Summary statistics of signals."""

    current_data: Dict[str, Any]
    """Current price/volume data."""

    metadata: Dict[str, Any]
    """Additional metadata."""


# ============ INDICATOR TYPES ============

IndicatorValue = Union[float, int, np.ndarray, pd.Series]
"""Value returned by an indicator calculation."""

IndicatorPeriod = int
"""Period parameter for an indicator (must be positive)."""

IndicatorResult = pd.DataFrame
"""DataFrame with indicator data added."""


# ============ COLLECTION TYPES ============

PriceList = List[PriceValue]
"""List of price values."""

VolumeList = List[VolumeValue]
"""List of volume values."""

SignalList = List[SignalInfo]
"""List of detected signals."""

SymbolList = List[Symbol]
"""List of stock symbols."""

TimeframeList = List[Timeframe]
"""List of timeframes."""

PriceRange = Tuple[PriceValue, PriceValue]
"""Tuple representing price range (low, high)."""

DateRange = Tuple[datetime, datetime]
"""Tuple representing date range (start, end)."""


# ============ CALLABLE TYPES ============

# Indicator calculation functions
IndicatorCalculator = Callable[[pd.DataFrame], pd.DataFrame]
"""Function that calculates indicators on a DataFrame."""

# Signal detection functions
SignalDetector = Callable[[pd.DataFrame, Any], List[SignalInfo]]
"""Function that detects signals in a DataFrame."""

# Filter/predicate functions
SignalFilter = Callable[[SignalInfo], bool]
"""Function that returns True if signal passes filter."""

# Data transformation functions
DataTransformer = Callable[[pd.DataFrame], pd.DataFrame]
"""Function that transforms market data."""


# ============ VALIDATION TYPES ============

ValidationResult = Union[bool, Tuple[bool, str]]
"""Result of validation (True or (False, reason))."""

ValidatedData = Tuple[bool, Union[pd.DataFrame, str]]
"""Tuple of (is_valid, dataframe_or_error_message)."""


# ============ CONFIGURATION TYPES ============

class ConfigParams(TypedDict, total=False):
    """
    Configuration parameters as typed dictionary.

    Used for passing custom config overrides.
    """

    interval: str
    """Timeframe interval."""

    name: str
    """Config name."""

    ma_periods: Sequence[int]
    """Moving average periods."""

    rsi_periods: Sequence[int]
    """RSI periods."""

    rsi_oversold: int
    """RSI oversold threshold."""

    rsi_overbought: int
    """RSI overbought threshold."""

    bb_periods: Sequence[int]
    """Bollinger Bands periods."""

    volume_threshold: float
    """Volume spike threshold multiplier."""

    price_change_threshold: float
    """Price change threshold percentage."""

    atr_period: int
    """ATR period."""

    stoch_period: int
    """Stochastic period."""

    macd_fast: int
    """MACD fast period."""

    macd_slow: int
    """MACD slow period."""

    macd_signal: int
    """MACD signal period."""


# ============ RETURN TYPES ============

OptionalString = Optional[str]
"""Optional string value."""

OptionalFloat = Optional[float]
"""Optional float value."""

OptionalInt = Optional[int]
"""Optional integer value."""

OptionalDataFrame = Optional[pd.DataFrame]
"""Optional DataFrame."""

OptionalSignal = Optional[SignalInfo]
"""Optional signal."""


# ============ UNION TYPES ============

NumericValue = Union[int, float, np.number]
"""Any numeric value type."""

SeriesOrArray = Union[pd.Series, np.ndarray, List]
"""Series, array, or list of values."""

DataFrameOrDict = Union[pd.DataFrame, Dict[str, Any]]
"""Either a DataFrame or dictionary of data."""


# ============ CALLABLE RETURNS ============

# Analysis pipeline stages
class PipelineResult(TypedDict, total=False):
    """Result from a pipeline stage."""

    success: bool
    """Whether stage succeeded."""

    data: Any
    """Stage output data."""

    error: Optional[str]
    """Error message if failed."""

    metadata: MetadataDict
    """Stage metadata."""


# ============ GENERIC TYPES ============

T = TypeVar = None  # Placeholder for generic types
"""Generic type variable (use in function definitions)."""


# ============ USEFUL TYPE COMBINATIONS ============

def is_valid_price(value: Any) -> bool:
    """Check if value is a valid price."""
    return isinstance(value, (int, float)) and not (
        np.isnan(value) if isinstance(value, float) else False
    ) and value >= 0


def is_valid_volume(value: Any) -> bool:
    """Check if value is valid volume."""
    return isinstance(value, (int, float)) and value >= 0 and int(value) == value


def is_valid_symbol(symbol: Any) -> bool:
    """Check if value is valid stock symbol."""
    return isinstance(symbol, str) and len(symbol) > 0 and symbol.isalpha()


def is_valid_timeframe(timeframe: Any) -> bool:
    """Check if value is valid timeframe."""
    valid_tf = ["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
    return isinstance(timeframe, str) and timeframe in valid_tf