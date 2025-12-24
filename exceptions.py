"""
Custom exception hierarchy for the trading signal analyzer.

Provides domain-specific exception types for clear error handling and
categorization of failures in the analysis pipeline.
"""

from typing import Optional


class AnalyzerError(Exception):
    """
    Base exception for all analyzer-related errors.

    All custom exceptions in this module inherit from this base class,
    allowing callers to catch all analyzer errors with a single except clause.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        Initialize the exception with message, code, and details.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code (e.g., "DATA_FETCH_001").
            details: Additional context dictionary for debugging.
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message with code and details."""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")
        return " | ".join(parts)


class DataFetchError(AnalyzerError):
    """
    Raised when market data fetching fails.

    Covers issues with yfinance API calls, network errors, invalid symbols,
    or unavailable data for the requested period/interval combination.
    """

    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        period: Optional[str] = None,
    ):
        """
        Initialize with fetching context.

        Args:
            message: Description of what went wrong.
            symbol: The stock symbol that failed to fetch.
            interval: The timeframe that was requested.
            period: The data period that was requested.
        """
        details = {}
        if symbol:
            details["symbol"] = symbol
        if interval:
            details["interval"] = interval
        if period:
            details["period"] = period

        super().__init__(
            message=message,
            error_code="DATA_FETCH_ERROR",
            details=details,
        )


class DataValidationError(AnalyzerError):
    """
    Raised when market data fails validation.

    Covers issues like missing required columns, insufficient data points,
    all NaN values, invalid data types, or out-of-range values.
    """

    def __init__(
        self,
        message: str,
        column: Optional[str] = None,
        reason: Optional[str] = None,
        value_count: Optional[int] = None,
    ):
        """
        Initialize with validation context.

        Args:
            message: Description of validation failure.
            column: The column that failed validation (if applicable).
            reason: Specific reason for failure (e.g., "all NaN", "missing").
            value_count: Number of values (useful for "insufficient data").
        """
        details = {}
        if column:
            details["column"] = column
        if reason:
            details["reason"] = reason
        if value_count is not None:
            details["value_count"] = value_count

        super().__init__(
            message=message,
            error_code="DATA_VALIDATION_ERROR",
            details=details,
        )


class InsufficientDataError(DataValidationError):
    """Raised when there are too few data points for indicator calculation."""

    def __init__(
        self,
        message: str,
        required: int,
        actual: int,
        indicator: Optional[str] = None,
    ):
        """
        Initialize with data count context.

        Args:
            message: Description of the issue.
            required: Minimum bars required for calculation.
            actual: Number of bars actually available.
            indicator: Name of the indicator that failed (if applicable).
        """
        details = {
            "required_bars": required,
            "actual_bars": actual,
        }
        if indicator:
            details["indicator"] = indicator

        super().__init__(
            message=message,
            reason="insufficient_data",
            value_count=actual,
        )
        self.details.update(details)


class SignalDetectionError(AnalyzerError):
    """
    Raised when signal detection logic fails.

    Covers issues in indicator calculations, signal detector bugs,
    or invalid signal data being generated.
    """

    def __init__(
        self,
        message: str,
        detector: Optional[str] = None,
        indicator: Optional[str] = None,
        exception: Optional[Exception] = None,
    ):
        """
        Initialize with detection context.

        Args:
            message: Description of the detection failure.
            detector: Name of the signal detector that failed.
            indicator: Name of the indicator being processed.
            exception: The underlying exception that caused this error.
        """
        details = {}
        if detector:
            details["detector"] = detector
        if indicator:
            details["indicator"] = indicator
        if exception:
            details["root_cause"] = str(exception)
            details["root_type"] = type(exception).__name__

        super().__init__(
            message=message,
            error_code="SIGNAL_DETECTION_ERROR",
            details=details,
        )


class ConfigurationError(AnalyzerError):
    """
    Raised when configuration is invalid or incomplete.

    Covers issues with signal parameters, timeframe settings,
    missing required config values, or invalid parameter values.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        invalid_value: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        Initialize with configuration context.

        Args:
            message: Description of the configuration problem.
            config_key: The configuration key that's problematic.
            invalid_value: The invalid value that was provided.
            reason: Why this value is invalid (e.g., "must be positive").
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if invalid_value is not None:
            details["invalid_value"] = invalid_value
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class TimeframeError(ConfigurationError):
    """Raised when an invalid or unsupported timeframe is specified."""

    SUPPORTED_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]

    def __init__(self, message: str, timeframe: str):
        """
        Initialize with timeframe context.

        Args:
            message: Description of the issue.
            timeframe: The invalid timeframe that was provided.
        """
        super().__init__(
            message=message,
            config_key="interval",
            invalid_value=timeframe,
            reason=f"must be one of {self.SUPPORTED_TIMEFRAMES}",
        )


class SymbolError(DataFetchError):
    """Raised when a stock symbol is invalid or unavailable."""

    def __init__(self, message: str, symbol: str):
        """
        Initialize with symbol context.

        Args:
            message: Description of the issue.
            symbol: The invalid or unavailable symbol.
        """
        super().__init__(
            message=message,
            symbol=symbol,
        )
        self.error_code = "SYMBOL_ERROR"


class ExportError(AnalyzerError):
    """
    Raised when exporting analysis results fails.

    Covers issues with file writing, invalid export formats,
    or serialization failures.
    """

    def __init__(
        self,
        message: str,
        export_format: Optional[str] = None,
        filepath: Optional[str] = None,
        exception: Optional[Exception] = None,
    ):
        """
        Initialize with export context.

        Args:
            message: Description of the export failure.
            export_format: Format being exported to (json, csv, markdown).
            filepath: Path where export was attempted.
            exception: The underlying exception that caused this error.
        """
        details = {}
        if export_format:
            details["format"] = export_format
        if filepath:
            details["filepath"] = filepath
        if exception:
            details["root_cause"] = str(exception)

        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            details=details,
        )


class AnalysisAbortedError(AnalyzerError):
    """
    Raised when the analysis pipeline is aborted.

    Used to signal early termination due to missing data, invalid state,
    or user-requested cancellation.
    """

    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        Initialize with pipeline context.

        Args:
            message: Description of why analysis was aborted.
            step: The pipeline step at which abort occurred.
            reason: The reason for abortion (e.g., "user_requested").
        """
        details = {}
        if step:
            details["pipeline_step"] = step
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="ANALYSIS_ABORTED",
            details=details,
        )