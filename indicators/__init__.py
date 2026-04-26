"""
Indicators package.

Provides technical indicator calculation with a registry pattern.

Exports:
    IndicatorBase: Abstract base class for all indicators.
    IndicatorMetadata: Metadata for indicator description.
    TrendIndicator: Base class for trend indicators.
    MomentumIndicator: Base class for momentum indicators.
    VolatilityIndicator: Base class for volatility indicators.
    VolumeIndicator: Base class for volume indicators.

    IndicatorRegistry: Registry for dynamic indicator creation.
    IndicatorFactory: Factory with pre-built indicator suites.

Indicators:
    SimpleMovingAverage, ExponentialMovingAverage: Moving averages.
    MovingAverageCrossover, MovingAverageRibbon: MA combinations.
    RelativeStrengthIndex, MACD, StochasticOscillator: Momentum.
    AverageTrueRange, AverageDirectionalIndex: Trend/Volatility.
    OnBalanceVolume, VolumeMovingAverage: Volume.
"""

from __future__ import annotations

from indicators.base import (
    IndicatorBase,
    IndicatorMetadata,
    TrendIndicator,
    MomentumIndicator,
    VolatilityIndicator,
    VolumeIndicator,
    CompositeIndicator,
    IndicatorGroup,
)
from indicators.registry import IndicatorRegistry, IndicatorFactory
from indicators.moving_averages import (
    SimpleMovingAverage,
    ExponentialMovingAverage,
    MovingAverageCrossover,
    MovingAverageRibbon,
)
from indicators.momentum import RelativeStrengthIndex, MACD, StochasticOscillator
from indicators.trend_volume import (
    AverageTrueRange,
    AverageDirectionalIndex,
    OnBalanceVolume,
    VolumeMovingAverage,
)

__all__ = [
    # Base classes
    "IndicatorBase",
    "IndicatorMetadata",
    "TrendIndicator",
    "MomentumIndicator",
    "VolatilityIndicator",
    "VolumeIndicator",
    "CompositeIndicator",
    "IndicatorGroup",
    # Registry
    "IndicatorRegistry",
    "IndicatorFactory",
    # Moving Averages
    "SimpleMovingAverage",
    "ExponentialMovingAverage",
    "MovingAverageCrossover",
    "MovingAverageRibbon",
    # Momentum
    "RelativeStrengthIndex",
    "MACD",
    "StochasticOscillator",
    # Trend/Volume
    "AverageTrueRange",
    "AverageDirectionalIndex",
    "OnBalanceVolume",
    "VolumeMovingAverage",
]
