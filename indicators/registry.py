"""
Indicator registry and factory.

Manages available indicators, creates instances, and provides
a plugin-like architecture for indicator discovery and management.
"""

from typing import Dict, List, Optional, Type, Any
from indicators.base import IndicatorBase, IndicatorGroup
from indicators.moving_averages import (
    SimpleMovingAverage,
    ExponentialMovingAverage,
    MovingAverageCrossover,
    MovingAverageRibbon,
)
from indicators.momentum import (
    RelativeStrengthIndex,
    MACD,
    StochasticOscillator,
)
from indicators.trend_volume import (
    AverageTrueRange,
    AverageDirectionalIndex,
    OnBalanceVolume,
    VolumeMovingAverage,
)
from exceptions import ConfigurationError
from logging_config import get_logger

logger = get_logger()


# ============ INDICATOR REGISTRY ============


class IndicatorRegistry:
    """
    Registry for all available indicators.

    Manages indicator classes, creates instances, and provides
    discovery/enumeration of available indicators.

    Example:
        >>> registry = IndicatorRegistry()
        >>> sma = registry.create('sma', period=20)
        >>> rsi = registry.create('rsi', period=14)
        >>> macd = registry.create('macd')
    """

    # Registry of all available indicators
    _INDICATORS: Dict[str, Type[IndicatorBase]] = {
        # Trend indicators
        "sma": SimpleMovingAverage,
        "ema": ExponentialMovingAverage,
        "ma_cross": MovingAverageCrossover,
        "ma_ribbon": MovingAverageRibbon,
        "atr": AverageTrueRange,
        "adx": AverageDirectionalIndex,
        # Momentum indicators
        "rsi": RelativeStrengthIndex,
        "macd": MACD,
        "stoch": StochasticOscillator,
        # Volume indicators
        "obv": OnBalanceVolume,
        "vol_ma": VolumeMovingAverage,
    }

    @classmethod
    def create(
        cls,
        indicator_key: str,
        **kwargs: Any,
    ) -> IndicatorBase:
        """
        Create an indicator instance.

        Args:
            indicator_key: Key of indicator to create (e.g., 'sma', 'rsi').
            **kwargs: Parameters to pass to indicator constructor.

        Returns:
            Instantiated indicator.

        Raises:
            ConfigurationError: If indicator key not found or params invalid.

        Example:
            >>> sma = IndicatorRegistry.create('sma', period=20)
            >>> rsi = IndicatorRegistry.create('rsi', period=14)
            >>> macd = IndicatorRegistry.create('macd', fast=12, slow=26)
        """
        if indicator_key not in cls._INDICATORS:
            raise ConfigurationError(
                f"Unknown indicator: {indicator_key}",
                config_key="indicator_key",
                invalid_value=indicator_key,
                reason=f"Must be one of {list(cls._INDICATORS.keys())}",
            )

        indicator_class = cls._INDICATORS[indicator_key]

        try:
            logger.debug(f"Creating indicator: {indicator_key} with {kwargs}")
            return indicator_class(**kwargs)
        except TypeError as e:
            raise ConfigurationError(
                f"Invalid parameters for {indicator_key}: {str(e)}",
                config_key=indicator_key,
                reason=str(e),
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Error creating {indicator_key}: {str(e)}",
                config_key=indicator_key,
            ) from e

    @classmethod
    def create_multiple(
        cls,
        indicators_config: Dict[str, Dict[str, Any]],
    ) -> List[IndicatorBase]:
        """
        Create multiple indicators from configuration.

        Args:
            indicators_config: Dict mapping indicator keys to parameter dicts.
                Example: {
                    'sma': {'period': 20},
                    'rsi': {'period': 14},
                    'macd': {'fast': 12, 'slow': 26}
                }

        Returns:
            List of created indicators.

        Raises:
            ConfigurationError: If any indicator creation fails.

        Example:
            >>> config = {
            ...     'sma': {'period': 20},
            ...     'ema': {'period': 50},
            ...     'rsi': {'period': 14},
            ... }
            >>> indicators = IndicatorRegistry.create_multiple(config)
        """
        indicators = []

        for key, params in indicators_config.items():
            try:
                indicator = cls.create(key, **params)
                indicators.append(indicator)
                logger.info(f"Created indicator: {key}")
            except ConfigurationError as e:
                logger.error(f"Failed to create indicator {key}: {str(e)}")
                raise

        return indicators

    @classmethod
    def list_available(cls) -> List[str]:
        """
        Get list of available indicator keys.

        Returns:
            List of indicator key strings (e.g., ['sma', 'rsi', 'macd']).
        """
        return list(cls._INDICATORS.keys())

    @classmethod
    def get_info(cls, indicator_key: str) -> Dict[str, Any]:
        """
        Get metadata about an indicator.

        Args:
            indicator_key: Key of indicator.

        Returns:
            Dictionary with indicator information.

        Raises:
            ConfigurationError: If indicator not found.
        """
        if indicator_key not in cls._INDICATORS:
            raise ConfigurationError(
                f"Unknown indicator: {indicator_key}",
                config_key="indicator_key",
                invalid_value=indicator_key,
            )

        indicator_class = cls._INDICATORS[indicator_key]

        # Create dummy instance to get metadata
        # Use default parameters
        try:
            if indicator_key == "ma_ribbon":
                instance = indicator_class()
            elif indicator_key == "ma_cross":
                instance = indicator_class()
            elif indicator_key == "stoch":
                instance = indicator_class()
            else:
                instance = indicator_class()
        except Exception:
            return {
                "key": indicator_key,
                "class": indicator_class.__name__,
                "error": "Could not instantiate for metadata",
            }

        meta = instance.metadata
        return {
            "key": indicator_key,
            "name": meta.name,
            "category": meta.category,
            "description": meta.description,
            "min_bars_required": meta.min_bars_required,
            "output_columns": list(meta.output_columns),
            "parameters": meta.parameters,
        }

    @classmethod
    def register(
        cls,
        key: str,
        indicator_class: Type[IndicatorBase],
    ) -> None:
        """
        Register a custom indicator class.

        Allows extending the registry with custom indicators.

        Args:
            key: Unique key for the indicator.
            indicator_class: Class that inherits from IndicatorBase.

        Raises:
            TypeError: If class doesn't inherit from IndicatorBase.
            ConfigurationError: If key already registered.

        Example:
            >>> class CustomIndicator(IndicatorBase):
            ...     # Implementation...
            >>> IndicatorRegistry.register('custom', CustomIndicator)
        """
        if not issubclass(indicator_class, IndicatorBase):
            raise TypeError(
                f"Indicator class must inherit from IndicatorBase, got {indicator_class}"
            )

        if key in cls._INDICATORS:
            raise ConfigurationError(
                f"Indicator key already registered: {key}",
                config_key="key",
                invalid_value=key,
                reason="Use a different key or override existing indicator",
            )

        cls._INDICATORS[key] = indicator_class
        logger.info(f"Registered custom indicator: {key}")


# ============ INDICATOR FACTORY ============


class IndicatorFactory:
    """
    Factory for creating pre-configured indicator groups.

    Provides pre-made combinations of indicators for common strategies.

    Example:
        >>> momentum_suite = IndicatorFactory.create_momentum_suite()
        >>> trend_suite = IndicatorFactory.create_trend_suite()
    """

    @staticmethod
    def create_momentum_suite() -> IndicatorGroup:
        """
        Create a momentum indicator suite.

        Includes: RSI, MACD, Stochastic

        Returns:
            IndicatorGroup with momentum indicators.
        """
        indicators = [
            IndicatorRegistry.create("rsi", period=14),
            IndicatorRegistry.create("macd"),
            IndicatorRegistry.create("stoch", period=14),
        ]
        return IndicatorGroup("Momentum Suite", indicators)

    @staticmethod
    def create_trend_suite() -> IndicatorGroup:
        """
        Create a trend indicator suite.

        Includes: SMA 20/50/200, ADX, ATR

        Returns:
            IndicatorGroup with trend indicators.
        """
        indicators = [
            IndicatorRegistry.create("sma", period=20),
            IndicatorRegistry.create("sma", period=50),
            IndicatorRegistry.create("sma", period=200),
            IndicatorRegistry.create("adx", period=14),
            IndicatorRegistry.create("atr", period=14),
        ]
        return IndicatorGroup("Trend Suite", indicators)

    @staticmethod
    def create_volume_suite() -> IndicatorGroup:
        """
        Create a volume indicator suite.

        Includes: Volume MA, OBV

        Returns:
            IndicatorGroup with volume indicators.
        """
        indicators = [
            IndicatorRegistry.create("vol_ma", period=20),
            IndicatorRegistry.create("obv"),
        ]
        return IndicatorGroup("Volume Suite", indicators)

    @staticmethod
    def create_intraday_suite() -> IndicatorGroup:
        """
        Create an intraday (5m-1h) indicator suite.

        Optimized for shorter timeframes.
        Includes: Fast EMA, RSI, MACD, Volume MA

        Returns:
            IndicatorGroup for intraday trading.
        """
        indicators = [
            IndicatorRegistry.create("ema", period=9),
            IndicatorRegistry.create("ema", period=21),
            IndicatorRegistry.create("rsi", period=7),
            IndicatorRegistry.create("macd", fast=8, slow=17, signal=9),
            IndicatorRegistry.create("vol_ma", period=10),
        ]
        return IndicatorGroup("Intraday Suite", indicators)

    @staticmethod
    def create_swing_suite() -> IndicatorGroup:
        """
        Create a swing trading indicator suite.

        Optimized for 1h-1d timeframes.
        Includes: SMA, EMA, RSI, MACD, ADX

        Returns:
            IndicatorGroup for swing trading.
        """
        indicators = [
            IndicatorRegistry.create("sma", period=20),
            IndicatorRegistry.create("sma", period=50),
            IndicatorRegistry.create("ema", period=12),
            IndicatorRegistry.create("rsi", period=14),
            IndicatorRegistry.create("macd"),
            IndicatorRegistry.create("adx", period=14),
        ]
        return IndicatorGroup("Swing Trading Suite", indicators)

    @staticmethod
    def create_all_indicators() -> IndicatorGroup:
        """
        Create all available indicators.

        Returns:
            IndicatorGroup with all indicators using defaults.
        """
        config = {
            "sma": {"period": 20},
            "ema": {"period": 20},
            "ma_cross": {},
            "ma_ribbon": {},
            "rsi": {"period": 14},
            "macd": {},
            "stoch": {"period": 14},
            "atr": {"period": 14},
            "adx": {"period": 14},
            "obv": {},
            "vol_ma": {"period": 20},
        }
        indicators = IndicatorRegistry.create_multiple(config)
        return IndicatorGroup("All Indicators", indicators)