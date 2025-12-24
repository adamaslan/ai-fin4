"""
Configuration system for signal analysis.

Provides immutable, validated configurations for different timeframes
and allows custom configuration creation with validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from exceptions import ConfigurationError, TimeframeError


# ============ CONSTANTS ============

SUPPORTED_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]

MAX_PERIODS_BY_TIMEFRAME = {
    "1m": "7d",
    "2m": "60d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "1h": "730d",
    "1d": "max",
    "1wk": "max",
    "1mo": "max",
}


# ============ SIGNAL CONFIG DATACLASS ============


@dataclass(frozen=True)
class SignalConfig:
    """
    Immutable configuration for signal detection and indicator parameters.

    This frozen dataclass ensures configuration integrity throughout the
    analysis pipeline. All parameters are validated during initialization.
    """

    # Metadata
    name: str
    interval: str

    # Moving Average periods
    ma_periods: tuple = (10, 20, 50, 100, 200)

    # RSI parameters
    rsi_periods: tuple = (9, 14, 21)
    rsi_oversold: int = 30
    rsi_overbought: int = 70

    # Bollinger Bands periods
    bb_periods: tuple = (10, 20, 30)

    # Volume analysis
    volume_threshold: float = 2.0

    # Price action
    price_change_threshold: float = 1.5

    # ATR (Average True Range)
    atr_period: int = 14

    # Stochastic Oscillator
    stoch_period: int = 14

    # MACD parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    def __post_init__(self) -> None:
        """
        Validate configuration after initialization.

        Raises:
            ConfigurationError: If any parameter is invalid.
        """
        self._validate()

    def _validate(self) -> None:
        """
        Validate all configuration parameters.

        Checks:
        - All periods are positive integers
        - RSI bounds are in valid range (0-100)
        - Volume threshold is positive
        - Price change threshold is positive
        - Interval is supported
        - MACD parameters satisfy fast < slow
        """
        # Validate interval
        if self.interval not in SUPPORTED_TIMEFRAMES:
            raise TimeframeError(
                f"Unsupported timeframe: {self.interval}",
                timeframe=self.interval,
            )

        # Validate moving average periods
        if not all(isinstance(p, int) and p > 0 for p in self.ma_periods):
            raise ConfigurationError(
                "MA periods must be positive integers",
                config_key="ma_periods",
                invalid_value=str(self.ma_periods),
                reason="All periods must be > 0",
            )

        # Validate RSI periods
        if not all(isinstance(p, int) and p > 0 for p in self.rsi_periods):
            raise ConfigurationError(
                "RSI periods must be positive integers",
                config_key="rsi_periods",
                invalid_value=str(self.rsi_periods),
                reason="All periods must be > 0",
            )

        # Validate RSI bounds
        if not (0 < self.rsi_oversold < 50):
            raise ConfigurationError(
                "RSI oversold must be between 0 and 50",
                config_key="rsi_oversold",
                invalid_value=str(self.rsi_oversold),
                reason="Must be in range (0, 50)",
            )

        if not (50 < self.rsi_overbought < 100):
            raise ConfigurationError(
                "RSI overbought must be between 50 and 100",
                config_key="rsi_overbought",
                invalid_value=str(self.rsi_overbought),
                reason="Must be in range (50, 100)",
            )

        if self.rsi_oversold >= self.rsi_overbought:
            raise ConfigurationError(
                "RSI oversold must be less than overbought",
                config_key="rsi_oversold",
                invalid_value=str(self.rsi_oversold),
                reason=f"Must be < rsi_overbought ({self.rsi_overbought})",
            )

        # Validate Bollinger Bands periods
        if not all(isinstance(p, int) and p > 0 for p in self.bb_periods):
            raise ConfigurationError(
                "BB periods must be positive integers",
                config_key="bb_periods",
                invalid_value=str(self.bb_periods),
                reason="All periods must be > 0",
            )

        # Validate volume threshold
        if not isinstance(self.volume_threshold, (int, float)) or self.volume_threshold <= 0:
            raise ConfigurationError(
                "Volume threshold must be positive number",
                config_key="volume_threshold",
                invalid_value=str(self.volume_threshold),
                reason="Must be > 0",
            )

        # Validate price change threshold
        if not isinstance(self.price_change_threshold, (int, float)) or self.price_change_threshold < 0:
            raise ConfigurationError(
                "Price change threshold must be non-negative",
                config_key="price_change_threshold",
                invalid_value=str(self.price_change_threshold),
                reason="Must be >= 0",
            )

        # Validate ATR period
        if not isinstance(self.atr_period, int) or self.atr_period <= 0:
            raise ConfigurationError(
                "ATR period must be positive integer",
                config_key="atr_period",
                invalid_value=str(self.atr_period),
                reason="Must be > 0",
            )

        # Validate Stochastic period
        if not isinstance(self.stoch_period, int) or self.stoch_period <= 0:
            raise ConfigurationError(
                "Stochastic period must be positive integer",
                config_key="stoch_period",
                invalid_value=str(self.stoch_period),
                reason="Must be > 0",
            )

        # Validate MACD parameters
        if not all(
            isinstance(p, int) and p > 0
            for p in [self.macd_fast, self.macd_slow, self.macd_signal]
        ):
            raise ConfigurationError(
                "MACD periods must be positive integers",
                config_key="macd_parameters",
                reason="All periods must be > 0",
            )

        if self.macd_fast >= self.macd_slow:
            raise ConfigurationError(
                "MACD fast period must be less than slow period",
                config_key="macd_fast",
                invalid_value=str(self.macd_fast),
                reason=f"Must be < macd_slow ({self.macd_slow})",
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration, with tuples
            converted to lists for JSON serialization.
        """
        config_dict = asdict(self)
        # Convert tuples to lists for JSON compatibility
        for key, value in config_dict.items():
            if isinstance(value, tuple):
                config_dict[key] = list(value)
        return config_dict

    def to_json_serializable(self) -> Dict[str, Any]:
        """
        Get configuration in JSON-serializable format.

        Alias for to_dict() for clarity.

        Returns:
            Dictionary with all values JSON-serializable.
        """
        return self.to_dict()


# ============ DEFAULT CONFIGURATIONS ============


DEFAULT_CONFIGS: Dict[str, SignalConfig] = {
    "1m": SignalConfig(
        name="1 Minute",
        interval="1m",
        ma_periods=(5, 10, 20, 50),
        rsi_periods=(7, 14),
        rsi_oversold=25,
        rsi_overbought=75,
        bb_periods=(10, 20),
        volume_threshold=1.5,
        price_change_threshold=0.5,
        atr_period=10,
        stoch_period=10,
        macd_fast=8,
        macd_slow=17,
        macd_signal=9,
    ),
    "5m": SignalConfig(
        name="5 Minute",
        interval="5m",
        ma_periods=(9, 20, 50, 100),
        rsi_periods=(9, 14),
        rsi_oversold=30,
        rsi_overbought=70,
        bb_periods=(10, 20),
        volume_threshold=1.8,
        price_change_threshold=0.8,
        atr_period=14,
        stoch_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    ),
    "15m": SignalConfig(
        name="15 Minute",
        interval="15m",
        ma_periods=(10, 20, 50, 100),
        rsi_periods=(9, 14, 21),
        rsi_oversold=30,
        rsi_overbought=70,
        bb_periods=(10, 20, 30),
        volume_threshold=2.0,
        price_change_threshold=1.0,
        atr_period=14,
        stoch_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    ),
    "1h": SignalConfig(
        name="1 Hour",
        interval="1h",
        ma_periods=(10, 20, 50, 100, 200),
        rsi_periods=(9, 14, 21),
        rsi_oversold=30,
        rsi_overbought=70,
        bb_periods=(10, 20, 30),
        volume_threshold=2.0,
        price_change_threshold=1.5,
        atr_period=14,
        stoch_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    ),
    "1d": SignalConfig(
        name="Daily",
        interval="1d",
        ma_periods=(10, 20, 50, 100, 200),
        rsi_periods=(9, 14, 21),
        rsi_oversold=30,
        rsi_overbought=70,
        bb_periods=(10, 20, 30),
        volume_threshold=2.0,
        price_change_threshold=3.0,
        atr_period=14,
        stoch_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    ),
}


# ============ CONFIGURATION FACTORY ============


class ConfigFactory:
    """
    Factory for creating and managing configurations.

    Provides methods to get standard configs and create custom ones
    with validation.
    """

    @staticmethod
    def get_config(interval: str) -> SignalConfig:
        """
        Get standard configuration for a timeframe.

        Args:
            interval: Timeframe key (e.g., '5m', '1h', '1d').

        Returns:
            SignalConfig for the specified interval.

        Raises:
            TimeframeError: If interval is not supported.
        """
        if interval not in DEFAULT_CONFIGS:
            raise TimeframeError(
                f"No default configuration for interval: {interval}",
                timeframe=interval,
            )
        return DEFAULT_CONFIGS[interval]

    @staticmethod
    def create_custom(
        interval: str,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> SignalConfig:
        """
        Create a custom configuration with overrides.

        Starts with the default config for the given interval and
        applies any overrides provided in kwargs.

        Args:
            interval: Timeframe for the configuration.
            name: Optional custom name for the configuration.
            **kwargs: Parameter overrides (ma_periods, rsi_oversold, etc.).

        Returns:
            New SignalConfig with custom parameters.

        Raises:
            TimeframeError: If interval is not supported.
            ConfigurationError: If any custom parameter is invalid.

        Example:
            >>> config = ConfigFactory.create_custom(
            ...     '5m',
            ...     name='Aggressive Scalping',
            ...     rsi_oversold=20,
            ...     rsi_overbought=80,
            ... )
        """
        # Get base config
        base_config = ConfigFactory.get_config(interval)
        
        # Extract name if provided
        custom_name = name or kwargs.pop("name", None)
        
        # Build new config dict from base
        config_dict = asdict(base_config)
        
        # Apply overrides
        config_dict.update(kwargs)
        
        # Set custom name if provided
        if custom_name:
            config_dict["name"] = custom_name
        
        # Create and return new config (validation happens in __post_init__)
        return SignalConfig(**config_dict)

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> SignalConfig:
        """
        Create configuration from dictionary.

        Allows loading configs from JSON or other dict sources.

        Args:
            config_dict: Dictionary with configuration parameters.
                Must include 'interval' key at minimum.

        Returns:
            SignalConfig created from dictionary values.

        Raises:
            KeyError: If required keys are missing.
            ConfigurationError: If any parameter is invalid.

        Example:
            >>> config_data = {'interval': '5m', 'rsi_oversold': 25}
            >>> config = ConfigFactory.from_dict(config_data)
        """
        # Require interval
        if "interval" not in config_dict:
            raise ConfigurationError(
                "interval key is required",
                config_key="interval",
                reason="Dictionary must contain 'interval' key",
            )

        interval = config_dict["interval"]
        
        # Get base config to fill in missing values
        base_config = ConfigFactory.get_config(interval)
        base_dict = asdict(base_config)
        
        # Convert lists back to tuples
        config_dict_processed = config_dict.copy()
        for key, value in config_dict_processed.items():
            if isinstance(value, list) and key in [
                "ma_periods",
                "rsi_periods",
                "bb_periods",
            ]:
                config_dict_processed[key] = tuple(value)
        
        # Merge with base (overrides take precedence)
        base_dict.update(config_dict_processed)
        
        return SignalConfig(**base_dict)

    @staticmethod
    def list_supported_intervals() -> List[str]:
        """
        Get list of supported timeframes.

        Returns:
            List of interval strings (e.g., ['1m', '5m', '15m', ...]).
        """
        return list(DEFAULT_CONFIGS.keys())

    @staticmethod
    def get_max_period(interval: str) -> str:
        """
        Get maximum data period for a timeframe.

        Returns:
            Period string suitable for yfinance (e.g., '60d', 'max').

        Raises:
            TimeframeError: If interval is not supported.
        """
        if interval not in MAX_PERIODS_BY_TIMEFRAME:
            raise TimeframeError(
                f"Unknown interval: {interval}",
                timeframe=interval,
            )
        return MAX_PERIODS_BY_TIMEFRAME[interval]