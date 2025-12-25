"""
Abstract base class for signal detection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Set
import pandas as pd

from logging_config import get_logger
from exceptions import SignalDetectionError
from signals.signal import Signal
from signals.signal_detector_metadata import SignalDetectorMetadata

logger = get_logger()


class SignalDetector(ABC):
    """
    Abstract base class for signal detection.

    All signal detectors inherit from this class and implement
    the `detect()` method. Provides common validation and error handling.

    Example:
        >>> class MySignalDetector(SignalDetector):
        ...     @property
        ...     def metadata(self) -> SignalDetectorMetadata:
        ...         return SignalDetectorMetadata(
        ...             name="My Detector",
        ...             category="custom",
        ...             required_indicators=["MA_20"],
        ...             description="Custom signal detection"
        ...         )
        ...
        ...     def detect(self, df: pd.DataFrame) -> List[Signal]:
        ...         signals = []
        ...         # Detection logic here
        ...         return signals
    """

    @property
    @abstractmethod
    def metadata(self) -> SignalDetectorMetadata:
        """
        Get metadata about this detector.

        Must be implemented by subclasses.

        Returns:
            SignalDetectorMetadata with detector information.
        """
        pass

    def validate_input(self, df: pd.DataFrame) -> None:
        """
        Validate input data meets requirements.

        Checks:
        - DataFrame is not empty
        - Has required columns

        Args:
            df: Market data to validate.

        Raises:
            SignalDetectionError: If validation fails.
        """
        meta = self.metadata

        # Check empty
        if df.empty:
            raise SignalDetectionError(
                f"Cannot detect {meta.name}: data is empty",
                detector=meta.name,
            )

        # Check required columns
        required_cols = self._get_required_columns()
        missing = required_cols - set(df.columns)

        if missing:
            raise SignalDetectionError(
                f"Cannot detect {meta.name}: missing columns {missing}",
                detector=meta.name,
            )

    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect signals in market data.

        Must be implemented by subclasses. Should:
        1. Validate input data
        2. Analyze indicators/prices
        3. Generate Signal objects
        4. Return list of signals

        Args:
            df: Market data with indicators calculated.

        Returns:
            List of detected Signal objects.

        Raises:
            SignalDetectionError: If detection fails.
        """
        pass

    def execute(self, df: pd.DataFrame) -> List[Signal]:
        """
        Execute signal detection with validation.

        Public method that validates input and handles errors.
        Preferred over direct `detect()` call.

        Args:
            df: Market data DataFrame.

        Returns:
            List of detected signals.

        Raises:
            SignalDetectionError: If detection fails.

        Example:
            >>> detector = MySignalDetector()
            >>> signals = detector.execute(market_data)
        """
        meta = self.metadata

        try:
            # Validate input
            self.validate_input(df)

            # Detect signals
            logger.debug(f"Detecting {meta.name}")
            signals = self.detect(df)

            logger.debug(f"Detected {len(signals)} signals from {meta.name}")
            return signals

        except SignalDetectionError:
            raise
        except Exception as e:
            raise SignalDetectionError(
                f"Error detecting {meta.name}: {str(e)}",
                detector=meta.name,
                exception=e,
            ) from e

    def _get_required_columns(self) -> Set[str]:
        """
        Get required columns from metadata.

        Returns:
            Set of required column names.
        """
        meta = self.metadata
        required = {"Open", "High", "Low", "Close", "Volume"}
        required.update(meta.required_indicators)
        return required

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.metadata)

    def __repr__(self) -> str:
        """Return detailed representation."""
        meta = self.metadata
        return f"{meta.name} (category={meta.category})"
