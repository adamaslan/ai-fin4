"""
Core analyzer module.

Provides the MultiTimeframeAnalyzer class that orchestrates data fetching,
indicator calculation, and signal detection using dependency injection.

Design Patterns Applied:
    - Single Responsibility: Only orchestration logic
    - Dependency Injection: All components passed in
    - Composition over Inheritance: Uses composed components
    - Early Returns: Guard clauses for validation
    - Immutable Data: Frozen result dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd
from datetime import datetime

from logging_config import get_logger
from config import SignalConfig, MAX_PERIODS_BY_TIMEFRAME, SUPPORTED_TIMEFRAMES
from data.provider import DataProvider, YFinanceProvider
from data.validator import MarketDataValidator, DataValidationPipeline
from indicators.base import IndicatorGroup
from indicators.registry import IndicatorRegistry, IndicatorFactory
from signals.aggregator import SignalAggregator, AggregationResult, DetectorFactory
from signals.validator import SignalQualityPipeline
from exceptions import (
    AnalyzerError,
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
    ConfigurationError,
)

logger = get_logger()


# ============ ANALYSIS RESULT ============


@dataclass(frozen=True)
class AnalysisResult:
    """
    Immutable result from a complete analysis.

    Contains all data, indicators, signals, and metadata from the analysis.
    """

    symbol: str
    """Stock symbol analyzed."""

    interval: str
    """Timeframe of analysis."""

    timestamp: datetime
    """When analysis was performed."""

    data: pd.DataFrame
    """Market data with indicators calculated."""

    signals: AggregationResult
    """Detected and aggregated signals."""

    indicators: Dict[str, Any]
    """Summary of current indicator values."""

    config: SignalConfig
    """Configuration used for analysis."""

    bars_analyzed: int
    """Number of bars in the dataset."""

    @property
    def summary(self) -> str:
        """Get human-readable summary."""
        return (
            f"{self.symbol} [{self.interval}]: "
            f"{self.signals.signal_count} signals "
            f"(+{self.signals.bullish_count}/-{self.signals.bearish_count}) "
            f"from {self.bars_analyzed} bars"
        )

    def __str__(self) -> str:
        """Return string representation."""
        return self.summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "timestamp": self.timestamp.isoformat(),
            "bars_analyzed": self.bars_analyzed,
            "signal_count": self.signals.signal_count,
            "bullish_count": self.signals.bullish_count,
            "bearish_count": self.signals.bearish_count,
            "neutral_count": self.signals.neutral_count,
            "indicators": self.indicators,
        }


# ============ MULTI-TIMEFRAME ANALYZER ============


class MultiTimeframeAnalyzer:
    """
    Orchestrates complete market analysis.

    Uses dependency injection for all components:
    - DataProvider: Fetches market data
    - IndicatorGroup: Calculates technical indicators
    - SignalAggregator: Detects and aggregates signals

    This class focuses solely on orchestration, delegating actual work
    to injected components.

    Example:
        >>> analyzer = MultiTimeframeAnalyzer(
        ...     symbol='SPY',
        ...     interval='1h',
        ...     data_provider=YFinanceProvider(),
        ... )
        >>> data = analyzer.fetch_data()
        >>> data = analyzer.calculate_indicators()
        >>> signals = analyzer.detect_signals()
        >>> result = analyzer.result
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "1d",
        period: Optional[str] = None,
        config: Optional[SignalConfig] = None,
        data_provider: Optional[DataProvider] = None,
        indicator_factory: str = "comprehensive",
        detector_factory: str = "comprehensive",
        quality_min: float = 0.3,
    ):
        """
        Initialize analyzer with dependency injection.

        Args:
            symbol: Stock symbol to analyze.
            interval: Timeframe (1m, 5m, 15m, 1h, 1d, etc.).
            period: Data period (default: auto-determined).
            config: Custom SignalConfig (default: auto-created).
            data_provider: Data provider instance (default: YFinanceProvider).
            indicator_factory: Name of indicator suite to use.
            detector_factory: Name of detector suite to use.
            quality_min: Minimum signal quality threshold.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        # Validate inputs early (Guard Clause pattern)
        self._validate_inputs(symbol, interval)

        # Store configuration
        self.symbol = symbol.upper()
        self.interval = interval
        self.period = period or self._get_default_period(interval)
        self.quality_min = quality_min

        # Create or use provided config
        self.config = config or self._create_default_config(interval)

        # Inject dependencies
        self.data_provider = data_provider or YFinanceProvider()
        self.validator = DataValidationPipeline()
        self.indicators = self._create_indicator_group(indicator_factory)
        self.aggregator = self._create_signal_aggregator(detector_factory)
        self.quality_pipeline = SignalQualityPipeline()

        # State
        self._data: Optional[pd.DataFrame] = None
        self._signals: Optional[AggregationResult] = None
        self._result: Optional[AnalysisResult] = None

        logger.info(f"Initialized analyzer: {self.symbol} [{self.interval}]")

    def _validate_inputs(self, symbol: str, interval: str) -> None:
        """Validate symbol and interval (Guard Clause)."""
        if not symbol or not symbol.strip():
            raise ConfigurationError(
                "Symbol is required",
                config_key="symbol",
                invalid_value=symbol,
            )

        if interval not in SUPPORTED_TIMEFRAMES:
            raise ConfigurationError(
                f"Unsupported interval: {interval}",
                config_key="interval",
                invalid_value=interval,
                reason=f"Must be one of {SUPPORTED_TIMEFRAMES}",
            )

    def _get_default_period(self, interval: str) -> str:
        """Get default data period for interval."""
        return MAX_PERIODS_BY_TIMEFRAME.get(interval, "1y")

    def _create_default_config(self, interval: str) -> SignalConfig:
        """Create default SignalConfig for interval."""
        return SignalConfig(
            name=f"Default {interval}",
            interval=interval,
        )

    def _create_indicator_group(self, factory_name: str) -> IndicatorGroup:
        """Create indicator group from factory."""
        factory_map = {
            "momentum": IndicatorFactory.create_momentum_suite,
            "trend": IndicatorFactory.create_trend_suite,
            "volume": IndicatorFactory.create_volume_suite,
            "intraday": IndicatorFactory.create_intraday_suite,
            "swing": IndicatorFactory.create_swing_suite,
            "comprehensive": IndicatorFactory.create_all_indicators,
            "all": IndicatorFactory.create_all_indicators,
        }

        factory_func = factory_map.get(factory_name.lower())
        if not factory_func:
            logger.warning(f"Unknown factory '{factory_name}', using comprehensive")
            factory_func = IndicatorFactory.create_all_indicators

        return factory_func()

    def _create_signal_aggregator(self, factory_name: str) -> SignalAggregator:
        """Create signal aggregator with detectors from factory."""
        aggregator = SignalAggregator(timeframe=self.interval)

        factory_map = {
            "basic": DetectorFactory.create_basic_detectors,
            "comprehensive": DetectorFactory.create_comprehensive_detectors,
            "intraday": DetectorFactory.create_intraday_detectors,
            "swing": DetectorFactory.create_swing_detectors,
            "trend": DetectorFactory.create_trend_detectors,
        }

        factory_func = factory_map.get(factory_name.lower())
        if not factory_func:
            logger.warning(f"Unknown detector factory '{factory_name}', using comprehensive")
            factory_func = DetectorFactory.create_comprehensive_detectors

        detectors = factory_func()
        aggregator.add_detectors(detectors)

        return aggregator

    # ============ PUBLIC API ============

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch and validate market data.

        Returns:
            Validated DataFrame with OHLCV data.

        Raises:
            DataFetchError: If data fetch fails.
            DataValidationError: If data validation fails.
            InsufficientDataError: If not enough data.
        """
        logger.info(f"Fetching data: {self.symbol} [{self.interval}] period={self.period}")

        try:
            # Fetch from provider
            raw_data = self.data_provider.fetch(
                symbol=self.symbol,
                interval=self.interval,
                period=self.period,
            )

            # Validate and clean
            self._data = self.validator.process(raw_data)

            logger.info(f"Fetched {len(self._data)} bars for {self.symbol}")
            return self._data

        except (DataFetchError, DataValidationError, InsufficientDataError):
            raise
        except Exception as e:
            raise DataFetchError(
                f"Failed to fetch data for {self.symbol}: {str(e)}",
                symbol=self.symbol,
                source="data_provider",
            ) from e

    def calculate_indicators(self) -> pd.DataFrame:
        """
        Calculate all technical indicators.

        Must call fetch_data() first.

        Returns:
            DataFrame with indicator columns added.

        Raises:
            AnalyzerError: If data not fetched or calculation fails.
        """
        if self._data is None:
            raise AnalyzerError("Must fetch data before calculating indicators")

        logger.info(f"Calculating indicators for {self.symbol}")

        try:
            # Execute indicator group
            self._data = self.indicators.execute(self._data)

            logger.info(f"Calculated {len(self.indicators.get_output_columns())} indicator columns")
            return self._data

        except Exception as e:
            raise AnalyzerError(
                f"Indicator calculation failed: {str(e)}",
                step="calculate_indicators",
            ) from e

    def detect_signals(self) -> AggregationResult:
        """
        Detect signals using all registered detectors.

        Must call calculate_indicators() first.

        Returns:
            AggregationResult with all detected signals.

        Raises:
            AnalyzerError: If indicators not calculated or detection fails.
        """
        if self._data is None:
            raise AnalyzerError("Must fetch data and calculate indicators first")

        logger.info(f"Detecting signals for {self.symbol}")

        try:
            # Run signal detection
            self._signals = self.aggregator.detect(self._data)

            # Apply quality filtering
            quality_result = self.quality_pipeline.process(self._signals.signals)

            # Log results
            logger.info(
                f"Detected {self._signals.signal_count} signals "
                f"(+{self._signals.bullish_count}/-{self._signals.bearish_count})"
            )

            # Build final result
            self._result = self._build_result()

            return self._signals

        except Exception as e:
            raise AnalyzerError(
                f"Signal detection failed: {str(e)}",
                step="detect_signals",
            ) from e

    def _build_result(self) -> AnalysisResult:
        """Build the final AnalysisResult."""
        # Extract current indicator values
        indicators = self._extract_current_indicators()

        return AnalysisResult(
            symbol=self.symbol,
            interval=self.interval,
            timestamp=datetime.now(),
            data=self._data,
            signals=self._signals,
            indicators=indicators,
            config=self.config,
            bars_analyzed=len(self._data) if self._data is not None else 0,
        )

    def _extract_current_indicators(self) -> Dict[str, Any]:
        """Extract current (latest) indicator values."""
        if self._data is None or self._data.empty:
            return {}

        last_row = self._data.iloc[-1]
        indicators = {}

        # Core price data
        indicators["Current_Price"] = self._safe_value(last_row.get("Close"))
        indicators["Open"] = self._safe_value(last_row.get("Open"))
        indicators["High"] = self._safe_value(last_row.get("High"))
        indicators["Low"] = self._safe_value(last_row.get("Low"))
        indicators["Volume"] = self._safe_value(last_row.get("Volume"))

        # Technical indicators (if calculated)
        indicator_cols = ["RSI", "MACD", "MACD_Signal", "ATR", "ADX", "OBV"]
        for col in indicator_cols:
            if col in self._data.columns:
                indicators[col] = self._safe_value(last_row.get(col))

        # Moving averages
        for period in [10, 20, 50, 100, 200]:
            col = f"SMA_{period}"
            if col in self._data.columns:
                indicators[col] = self._safe_value(last_row.get(col))

        return indicators

    def _safe_value(self, value: Any) -> Any:
        """Safely convert value, handling NaN."""
        if pd.isna(value):
            return None
        if isinstance(value, float):
            return round(value, 4)
        return value

    @property
    def result(self) -> Optional[AnalysisResult]:
        """Get the analysis result (after detect_signals called)."""
        return self._result

    @property
    def data(self) -> Optional[pd.DataFrame]:
        """Get the current data (after fetch_data called)."""
        return self._data

    def __str__(self) -> str:
        """Return string representation."""
        return f"MultiTimeframeAnalyzer({self.symbol}[{self.interval}])"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"MultiTimeframeAnalyzer("
            f"symbol={self.symbol!r}, "
            f"interval={self.interval!r}, "
            f"period={self.period!r})"
        )
