"""
Signal validation and quality control.

Validates signal data, detects contradictions, and applies quality filters.
"""

from typing import List, Set, Tuple
from signals.base import Signal, SignalStrength, SignalFilter
from logging_config import get_logger

logger = get_logger()


# ============ SIGNAL VALIDATOR ============


class SignalValidator:
    """
    Validates signal data for correctness and consistency.

    Checks:
    - Signal has required fields
    - Value is within reasonable range
    - Strength is valid
    - Category is recognized
    - Confidence is 0.0-1.0
    """

    VALID_CATEGORIES = {
        "MA_CROSS",
        "MA_POSITION",
        "MA_RIBBON",
        "RSI",
        "MACD",
        "STOCHASTIC",
        "ATR",
        "ADX",
        "VOLUME",
        "FIBONACCI",
        "PRICE_ACTION",
        "VWAP",
    }

    VALID_STRENGTHS = {
        SignalStrength.BULLISH,
        SignalStrength.BEARISH,
        SignalStrength.STRONG_BULLISH,
        SignalStrength.STRONG_BEARISH,
        SignalStrength.EXTREME_BULLISH,
        SignalStrength.EXTREME_BEARISH,
        SignalStrength.NEUTRAL,
        SignalStrength.MODERATE,
        SignalStrength.SIGNIFICANT,
        SignalStrength.WEAK,
        SignalStrength.TRENDING,
    }

    @staticmethod
    def validate(signal: Signal) -> Tuple[bool, str]:
        """
        Validate a single signal.

        Args:
            signal: Signal to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check required fields
        if not signal.name or not isinstance(signal.name, str):
            return False, "Signal name is required"

        if not signal.category or not isinstance(signal.category, str):
            return False, "Signal category is required"

        if not signal.strength or not isinstance(signal.strength, str):
            return False, "Signal strength is required"

        if not signal.description or not isinstance(signal.description, str):
            return False, "Signal description is required"

        # Check strength is valid
        if signal.strength not in SignalValidator.VALID_STRENGTHS:
            return False, f"Invalid strength: {signal.strength}"

        # Check confidence is 0.0-1.0
        if not (0.0 <= signal.confidence <= 1.0):
            return False, f"Confidence must be 0.0-1.0, got {signal.confidence}"

        # Check value is reasonable if present
        if signal.value is not None:
            try:
                float(signal.value)
            except (TypeError, ValueError):
                return False, f"Value must be numeric, got {signal.value}"

        return True, ""

    @staticmethod
    def validate_batch(signals: List[Signal]) -> Tuple[List[Signal], int]:
        """
        Validate batch of signals, removing invalid ones.

        Args:
            signals: List of signals to validate.

        Returns:
            Tuple of (valid_signals, invalid_count).
        """
        valid = []
        invalid_count = 0

        for signal in signals:
            is_valid, error = SignalValidator.validate(signal)

            if is_valid:
                valid.append(signal)
            else:
                invalid_count += 1
                logger.warning(f"Invalid signal removed: {signal.name} - {error}")

        if invalid_count > 0:
            logger.info(f"Validation: removed {invalid_count} invalid signals")

        return valid, invalid_count


# ============ SIGNAL CONTRADICTION DETECTOR ============


class ContradictionDetector:
    """
    Detects contradictory signals.

    Identifies when signals from the same category or related categories
    have conflicting strength/direction.
    """

    # Categories that should not have both bullish and bearish signals
    EXCLUSIVE_CATEGORIES = {
        "MA_CROSS",
        "MACD",
        "PRICE_ACTION",
    }

    @staticmethod
    def detect_contradictions(signals: List[Signal]) -> List[Tuple[int, int, str]]:
        """
        Detect contradictory signal pairs.

        Args:
            signals: List of signals to check.

        Returns:
            List of tuples (index1, index2, reason) for contradictions.
        """
        contradictions = []

        # Group signals by category
        by_category = {}
        for i, signal in enumerate(signals):
            if signal.category not in by_category:
                by_category[signal.category] = []
            by_category[signal.category].append((i, signal))

        # Check each exclusive category
        for category in ContradictionDetector.EXCLUSIVE_CATEGORIES:
            if category not in by_category:
                continue

            signals_in_cat = by_category[category]

            # Check for both bullish and bearish
            bullish = [
                (i, s) for i, s in signals_in_cat if SignalStrength.is_bullish(s.strength)
            ]
            bearish = [
                (i, s) for i, s in signals_in_cat if SignalStrength.is_bearish(s.strength)
            ]

            if bullish and bearish:
                # Both bullish and bearish signals exist
                for bull_idx, bull_signal in bullish:
                    for bear_idx, bear_signal in bearish:
                        contradictions.append(
                            (
                                bull_idx,
                                bear_idx,
                                f"Contradicting {category} signals: {bull_signal.name} vs {bear_signal.name}",
                            )
                        )

        return contradictions

    @staticmethod
    def resolve_contradictions(
        signals: List[Signal],
        resolution: str = "remove_lower_confidence",
    ) -> List[Signal]:
        """
        Resolve contradictions by removing weaker signals.

        Args:
            signals: List of signals.
            resolution: How to resolve ('remove_lower_confidence' or 'keep_all').

        Returns:
            Signals with contradictions resolved.
        """
        if resolution == "keep_all":
            return signals

        contradictions = ContradictionDetector.detect_contradictions(signals)

        if not contradictions:
            return signals

        logger.info(f"Resolving {len(contradictions)} signal contradictions")

        # Mark signals to remove
        to_remove: Set[int] = set()

        for idx1, idx2, reason in contradictions:
            logger.debug(f"Contradiction: {reason}")

            # Keep higher confidence signal
            if signals[idx1].confidence >= signals[idx2].confidence:
                to_remove.add(idx2)
            else:
                to_remove.add(idx1)

        # Return signals excluding marked ones
        result = [s for i, s in enumerate(signals) if i not in to_remove]

        if to_remove:
            logger.info(f"Removed {len(to_remove)} contradictory signals")

        return result


# ============ SIGNAL QUALITY SCORER ============


class QualityScorer:
    """
    Scores signal quality based on multiple factors.

    Combines multiple indicators to provide confidence score.
    """

    @staticmethod
    def score_signal(signal: Signal) -> float:
        """
        Score signal quality (0.0 to 1.0).

        Considers:
        - Base confidence
        - Strength level
        - Signal name quality
        - Details completeness

        Args:
            signal: Signal to score.

        Returns:
            Quality score (0.0 to 1.0).
        """
        score = signal.confidence  # Start with base confidence

        # Boost for strong signals
        if SignalStrength.is_bullish(signal.strength) or SignalStrength.is_bearish(
            signal.strength
        ):
            if "STRONG" in signal.strength or "EXTREME" in signal.strength:
                score = min(1.0, score + 0.1)

        # Boost for signals with details
        if signal.details:
            score = min(1.0, score + 0.05)

        # Boost for signals with trading implication
        if signal.trading_implication:
            score = min(1.0, score + 0.05)

        # Slight penalty for neutral signals
        if signal.is_neutral():
            score = max(0.0, score - 0.1)

        return score

    @staticmethod
    def score_batch(signals: List[Signal]) -> List[Tuple[Signal, float]]:
        """
        Score batch of signals.

        Args:
            signals: List of signals to score.

        Returns:
            List of (signal, score) tuples.
        """
        return [(signal, QualityScorer.score_signal(signal)) for signal in signals]

    @staticmethod
    def filter_by_quality(
        signals: List[Signal], min_quality: float = 0.5
    ) -> List[Signal]:
        """
        Filter signals by quality threshold.

        Args:
            signals: List of signals.
            min_quality: Minimum quality score (0.0 to 1.0).

        Returns:
            Filtered signals meeting quality threshold.
        """
        scored = QualityScorer.score_batch(signals)
        filtered = [signal for signal, score in scored if score >= min_quality]

        if len(filtered) < len(signals):
            logger.info(
                f"Quality filter: {len(signals)} → {len(filtered)} signals "
                f"(min quality: {min_quality})"
            )

        return filtered


# ============ SIGNAL QUALITY PIPELINE ============


class SignalQualityPipeline:
    """
    Complete quality control pipeline for signals.

    Validates, detects contradictions, and scores signals.
    """

    def __init__(
        self,
        validate: bool = True,
        resolve_contradictions: bool = True,
        score_quality: bool = True,
        min_quality: float = 0.3,
    ):
        """
        Initialize quality pipeline.

        Args:
            validate: Validate signal data.
            resolve_contradictions: Resolve conflicting signals.
            score_quality: Score signal quality.
            min_quality: Minimum quality threshold.
        """
        self.validate = validate
        self.resolve_contradictions = resolve_contradictions
        self.score_quality = score_quality
        self.min_quality = min_quality

    def process(self, signals: List[Signal]) -> List[Signal]:
        """
        Process signals through quality pipeline.

        Args:
            signals: List of signals to process.

        Returns:
            Quality-controlled signals.
        """
        result = signals.copy()

        logger.debug(f"Processing {len(result)} signals through quality pipeline")

        # Step 1: Validate
        if self.validate:
            result, invalid_count = SignalValidator.validate_batch(result)
            logger.debug(f"Validation: {invalid_count} invalid signals removed")

        # Step 2: Resolve contradictions
        if self.resolve_contradictions:
            result = ContradictionDetector.resolve_contradictions(
                result, resolution="remove_lower_confidence"
            )

        # Step 3: Score and filter by quality
        if self.score_quality:
            result = QualityScorer.filter_by_quality(result, self.min_quality)

        logger.info(
            f"Quality pipeline complete: {len(signals)} → {len(result)} signals"
        )

        return result