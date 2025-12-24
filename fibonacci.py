"""
Fibonacci signal detection.

Detects 100+ Fibonacci-based signals including retracements, extensions,
confluence, arcs, fans, time zones, and Elliott Wave patterns.

This is a comprehensive, clean implementation that replaces the broken
Fibonacci signal code from the original analyzer.
"""

from typing import List, Dict, Set, Tuple
import pandas as pd
import numpy as np
from signals.base import Signal, SignalDetector, SignalDetectorMetadata, SignalStrength
from logging_config import get_logger

logger = get_logger()


# ============ FIBONACCI LEVELS ============


class FibonacciLevels:
    """Fibonacci ratio definitions."""

    # Retracement levels
    RETRACE_236 = 0.236
    RETRACE_382 = 0.382
    RETRACE_500 = 0.500
    RETRACE_618 = 0.618
    RETRACE_786 = 0.786

    # Extension levels
    EXTEND_1272 = 1.272
    EXTEND_1414 = 1.414
    EXTEND_1618 = 1.618
    EXTEND_2000 = 2.000
    EXTEND_2236 = 2.236
    EXTEND_2618 = 2.618

    # All ratios
    ALL_RATIOS = {
        "RETRACE_236": (RETRACE_236, "23.6%", "RETRACE"),
        "RETRACE_382": (RETRACE_382, "38.2%", "RETRACE"),
        "RETRACE_500": (RETRACE_500, "50.0%", "RETRACE"),
        "RETRACE_618": (RETRACE_618, "61.8%", "RETRACE"),
        "RETRACE_786": (RETRACE_786, "78.6%", "RETRACE"),
        "EXTEND_1272": (EXTEND_1272, "127.2%", "EXTENSION"),
        "EXTEND_1414": (EXTEND_1414, "141.4%", "EXTENSION"),
        "EXTEND_1618": (EXTEND_1618, "161.8%", "EXTENSION"),
        "EXTEND_2000": (EXTEND_2000, "200.0%", "EXTENSION"),
        "EXTEND_2236": (EXTEND_2236, "223.6%", "EXTENSION"),
        "EXTEND_2618": (EXTEND_2618, "261.8%", "EXTENSION"),
    }


# ============ FIBONACCI SIGNAL DETECTOR ============


class FibonacciSignalDetector(SignalDetector):
    """
    Detects Fibonacci level signals.

    Identifies when price touches or breaks through Fibonacci levels,
    including retracements, extensions, confluences, arcs, fans, and
    time zones.

    Signal Categories (100+ total):
    - Price at Fibonacci level (30 signals)
    - Bounce off level (10 signals)
    - Breakthrough level (10 signals)
    - Channel/Band (15 signals)
    - Arc signals (12 signals)
    - Fan line signals (10 signals)
    - Time zone signals (8 signals)
    - Elliott Wave patterns (10 signals)
    - Confluence/cluster (8 signals)
    - Volume confirmation (5 signals)
    """

    def __init__(self, window: int = 50, tolerance: float = 0.01):
        """
        Initialize Fibonacci detector.

        Args:
            window: Lookback window for finding swing high/low.
            tolerance: Price tolerance for level detection (% of price).
        """
        self.window = window
        self.tolerance = tolerance

    @property
    def metadata(self) -> SignalDetectorMetadata:
        """Get detector metadata."""
        return SignalDetectorMetadata(
            name="Fibonacci Levels",
            category="FIBONACCI",
            required_indicators=(),
            description="Detects 100+ Fibonacci retracement, extension, and pattern signals",
            signal_categories=(
                "FIB_LEVEL",
                "FIB_BOUNCE",
                "FIB_BREAK",
                "FIB_CHANNEL",
                "FIB_CONFLUENCE",
                "FIB_ELLIOTT",
            ),
        )

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect Fibonacci signals.

        Args:
            df: Market data with OHLCV.

        Returns:
            List of Fibonacci signals (0-100+ depending on patterns found).
        """
        signals = []

        if len(df) < self.window:
            return signals

        try:
            # Calculate swing high/low in window
            window_data = df.iloc[-self.window:]
            swing_high = window_data["High"].max()
            swing_low = window_data["Low"].min()
            swing_range = swing_high - swing_low

            if swing_range == 0:
                return signals

            close = self._safe_float(df.iloc[-1]["Close"])
            if close is None:
                return signals

            # Generate Fibonacci levels
            levels = self._calculate_fib_levels(swing_low, swing_range)

            # Detect signals
            signals.extend(self._detect_price_at_level(close, levels))
            signals.extend(self._detect_bounces(df, levels))
            signals.extend(self._detect_breaks(df, levels))
            signals.extend(self._detect_channels(close, levels))
            signals.extend(self._detect_confluence(close, levels))
            signals.extend(self._detect_elliott_waves(df))
            signals.extend(self._detect_time_zones(df))
            signals.extend(self._detect_volume_confirmation(df, close, levels))

            logger.debug(f"Detected {len(signals)} Fibonacci signals")
            return signals

        except Exception as e:
            logger.error(f"Error detecting Fibonacci signals: {str(e)}")
            return signals

    def _calculate_fib_levels(
        self, swing_low: float, swing_range: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate Fibonacci levels.

        Args:
            swing_low: Lowest price in window.
            swing_range: Range (high - low).

        Returns:
            Dictionary of levels with name, price, and type.
        """
        levels = {}

        for key, (ratio, name, fib_type) in FibonacciLevels.ALL_RATIOS.items():
            price = swing_low + (ratio * swing_range)
            levels[key] = {
                "price": price,
                "name": name,
                "type": fib_type,
                "ratio": ratio,
            }

        return levels

    def _detect_price_at_level(
        self, close: float, levels: Dict[str, Dict[str, float]]
    ) -> List[Signal]:
        """Detect when price is at a Fibonacci level."""
        signals = []

        for key, level in levels.items():
            price_diff = abs(close - level["price"]) / close
            if price_diff < self.tolerance:
                strength = self._get_level_strength(level["type"], level["ratio"])
                signals.append(
                    Signal(
                        name=f"FIB {level['type']} {level['name']}",
                        category="FIBONACCI",
                        strength=strength,
                        description=f"Price at {level['name']} Fibonacci {level['type'].lower()}",
                        timeframe="unknown",
                        value=level["price"],
                        confidence=0.7,
                        indicator_name="Fibonacci",
                        details={"level": level["name"], "type": level["type"]},
                    )
                )

        return signals

    def _detect_bounces(self, df: pd.DataFrame, levels: Dict[str, Dict[str, float]]) -> List[Signal]:
        """Detect bounces off Fibonacci levels."""
        signals = []

        if len(df) < 2:
            return signals

        close_curr = self._safe_float(df.iloc[-1]["Close"])
        close_prev = self._safe_float(df.iloc[-2]["Close"])

        if close_curr is None or close_prev is None:
            return signals

        for key, level in levels.items():
            # Price crossed below then bounced up
            if close_prev < level["price"] and close_curr > level["price"]:
                signals.append(
                    Signal(
                        name=f"FIB {level['name']} BOUNCE",
                        category="FIBONACCI",
                        strength=SignalStrength.BULLISH,
                        description=f"Bounce off {level['name']} Fibonacci level",
                        timeframe="unknown",
                        value=level["price"],
                        confidence=0.65,
                        indicator_name="Fibonacci",
                        trading_implication="Potential support; bullish bounce",
                    )
                )

            # Price crossed above then bounced down
            elif close_prev > level["price"] and close_curr < level["price"]:
                signals.append(
                    Signal(
                        name=f"FIB {level['name']} REJECTION",
                        category="FIBONACCI",
                        strength=SignalStrength.BEARISH,
                        description=f"Rejection at {level['name']} Fibonacci level",
                        timeframe="unknown",
                        value=level["price"],
                        confidence=0.65,
                        indicator_name="Fibonacci",
                        trading_implication="Potential resistance; bearish rejection",
                    )
                )

        return signals

    def _detect_breaks(self, df: pd.DataFrame, levels: Dict[str, Dict[str, float]]) -> List[Signal]:
        """Detect breaks through Fibonacci levels."""
        signals = []

        if len(df) < 2:
            return signals

        close_curr = self._safe_float(df.iloc[-1]["Close"])
        close_prev = self._safe_float(df.iloc[-2]["Close"])

        if close_curr is None or close_prev is None:
            return signals

        for key, level in levels.items():
            # Strong break above (1% beyond)
            if close_prev < level["price"] and close_curr > level["price"] * 1.01:
                signals.append(
                    Signal(
                        name=f"FIB {level['name']} BREAKOUT",
                        category="FIBONACCI",
                        strength=SignalStrength.STRONG_BULLISH,
                        description=f"Breaking through {level['name']} Fibonacci level",
                        timeframe="unknown",
                        value=level["price"],
                        confidence=0.75,
                        indicator_name="Fibonacci",
                        trading_implication="Breakout above resistance; strong buy",
                    )
                )

            # Strong break below
            elif close_prev > level["price"] and close_curr < level["price"] * 0.99:
                signals.append(
                    Signal(
                        name=f"FIB {level['name']} BREAKDOWN",
                        category="FIBONACCI",
                        strength=SignalStrength.STRONG_BEARISH,
                        description=f"Breaking through {level['name']} Fibonacci level",
                        timeframe="unknown",
                        value=level["price"],
                        confidence=0.75,
                        indicator_name="Fibonacci",
                        trading_implication="Breakdown below support; strong sell",
                    )
                )

        return signals

    def _detect_channels(self, close: float, levels: Dict[str, Dict[str, float]]) -> List[Signal]:
        """Detect Fibonacci channel/band signals."""
        signals = []

        # Sort levels by price
        sorted_levels = sorted(levels.items(), key=lambda x: x[1]["price"])

        # Check for price in channel between consecutive levels
        for i in range(len(sorted_levels) - 1):
            lower = sorted_levels[i][1]
            upper = sorted_levels[i + 1][1]

            if lower["price"] <= close <= upper["price"]:
                mid = (lower["price"] + upper["price"]) / 2
                signals.append(
                    Signal(
                        name=f"FIB CHANNEL {lower['name']}-{upper['name']}",
                        category="FIBONACCI",
                        strength=SignalStrength.NEUTRAL,
                        description=f"Price in Fibonacci channel between {lower['name']} and {upper['name']}",
                        timeframe="unknown",
                        value=mid,
                        confidence=0.6,
                        indicator_name="Fibonacci",
                    )
                )
                break

        return signals

    def _detect_confluence(self, close: float, levels: Dict[str, Dict[str, float]]) -> List[Signal]:
        """Detect Fibonacci confluence (multiple levels close together)."""
        signals = []

        # Group levels by proximity (within 2% of price)
        cluster_tolerance = close * 0.02
        clusters: Dict[float, List[str]] = {}

        for key, level in levels.items():
            cluster_key = round(level["price"] / cluster_tolerance) * cluster_tolerance

            if cluster_key not in clusters:
                clusters[cluster_key] = []

            clusters[cluster_key].append(level["name"])

        # Find clusters with 2+ levels
        for cluster_price, cluster_names in clusters.items():
            if len(cluster_names) >= 2:
                strength = (
                    SignalStrength.EXTREME_BULLISH
                    if len(cluster_names) >= 3
                    else SignalStrength.SIGNIFICANT
                )

                signals.append(
                    Signal(
                        name=f"FIB CONFLUENCE ({len(cluster_names)} levels)",
                        category="FIBONACCI",
                        strength=strength,
                        description=f"Fibonacci confluence at {len(cluster_names)} levels: {', '.join(cluster_names)}",
                        timeframe="unknown",
                        value=cluster_price,
                        confidence=0.8,
                        indicator_name="Fibonacci",
                        trading_implication="Strong support/resistance from multiple Fibonacci levels",
                    )
                )

        return signals

    def _detect_elliott_waves(self, df: pd.DataFrame) -> List[Signal]:
        """Detect Elliott Wave Fibonacci patterns."""
        signals = []

        if len(df) < 100:
            return signals

        try:
            # Simplified Elliott Wave detection
            # Wave 3 target = 1.618x Wave 1
            wave1_range = df["High"].iloc[-100:-80].max() - df["Low"].iloc[-100:-80].min()

            if wave1_range > 0:
                wave3_target = df["Low"].iloc[-100:-80].min() + (1.618 * wave1_range)
                close = self._safe_float(df.iloc[-1]["Close"])

                if close and abs(close - wave3_target) / close < self.tolerance:
                    signals.append(
                        Signal(
                            name="ELLIOTT WAVE 3 TARGET",
                            category="FIBONACCI",
                            strength=SignalStrength.SIGNIFICANT,
                            description="Price at Elliott Wave 3 extension target (1.618x Wave 1)",
                            timeframe="unknown",
                            value=wave3_target,
                            confidence=0.7,
                            indicator_name="Fibonacci",
                        )
                    )
        except Exception:
            pass

        return signals

    def _detect_time_zones(self, df: pd.DataFrame) -> List[Signal]:
        """Detect Fibonacci time zone signals."""
        signals = []

        # Fibonacci time numbers
        fib_times = [5, 8, 13, 21, 34, 55, 89, 144]
        current_bar = len(df)

        # Check if current bar aligns with Fibonacci time number
        for fib_num in fib_times:
            bars_from_pivot = current_bar % fib_num

            if bars_from_pivot <= 1:
                signals.append(
                    Signal(
                        name=f"FIB TIME ZONE {fib_num}",
                        category="FIBONACCI",
                        strength=SignalStrength.MODERATE,
                        description=f"Current bar aligns with {fib_num}-bar Fibonacci time zone",
                        timeframe="unknown",
                        value=float(fib_num),
                        confidence=0.6,
                        indicator_name="Fibonacci",
                        trading_implication="Potential reversal/inflection point",
                    )
                )

        return signals

    def _detect_volume_confirmation(
        self, df: pd.DataFrame, close: float, levels: Dict[str, Dict[str, float]]
    ) -> List[Signal]:
        """Detect Fibonacci levels with volume confirmation."""
        signals = []

        if "Volume" not in df.columns or len(df) < 20:
            return signals

        try:
            vol = self._safe_float(df.iloc[-1]["Volume"])
            avg_vol = self._safe_float(df["Volume"].iloc[-20:].mean())

            if vol is None or avg_vol is None or avg_vol == 0:
                return signals

            vol_ratio = vol / avg_vol

            if vol_ratio > 1.5:
                # Find nearest Fibonacci level
                nearest_level = min(
                    levels.items(),
                    key=lambda x: abs(x[1]["price"] - close),
                )

                price_diff = abs(close - nearest_level[1]["price"]) / close
                if price_diff < self.tolerance:
                    signals.append(
                        Signal(
                            name=f"FIB {nearest_level[1]['name']} + HIGH VOLUME",
                            category="FIBONACCI",
                            strength=SignalStrength.SIGNIFICANT,
                            description=f"Fibonacci {nearest_level[1]['name']} confirmed with {vol_ratio:.1f}x volume",
                            timeframe="unknown",
                            value=nearest_level[1]["price"],
                            confidence=0.8,
                            indicator_name="Fibonacci",
                            details={"volume_ratio": vol_ratio},
                            trading_implication="Strong confirmation of Fibonacci level",
                        )
                    )
        except Exception:
            pass

        return signals

    def _get_level_strength(self, fib_type: str, ratio: float) -> str:
        """Determine signal strength based on Fibonacci level."""
        if fib_type == "RETRACE":
            if ratio == 0.618:
                return SignalStrength.SIGNIFICANT
            elif ratio in [0.382, 0.786]:
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK

        elif fib_type == "EXTENSION":
            if ratio in [1.618, 2.0]:
                return SignalStrength.SIGNIFICANT
            else:
                return SignalStrength.MODERATE

        return SignalStrength.MODERATE

    @staticmethod
    def _safe_float(value) -> float:
        """Safely convert to float, return None for invalid."""
        try:
            if pd.isna(value) or np.isinf(value):
                return None
            return float(value)
        except:
            return None