"""
Logging configuration for the signal analyzer.

Provides a centralized logging setup with support for different log levels,
formatted output, and optional JSON logging for structured logs.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime


# ============ LOG LEVEL CONSTANTS ============

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# ============ FORMATTERS ============


class DetailedFormatter(logging.Formatter):
    """
    Detailed formatter with timestamp, level, module, and function name.

    Format:
        [2025-12-23 15:30:45] [INFO] module.function:42 - Message here
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with detailed information."""
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname
        module = record.module
        func = record.funcName
        line = record.lineno
        message = record.getMessage()
        
        return f"[{timestamp}] [{level}] {module}.{func}:{line} - {message}"


class SimpleFormatter(logging.Formatter):
    """
    Simple formatter with just level and message.

    Format:
        [INFO] Message here
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record simply."""
        level = record.levelname
        message = record.getMessage()
        return f"[{level}] {message}"


class StructuredFormatter(logging.Formatter):
    """
    Structured formatter that outputs key-value pairs.

    Format (minimal):
        timestamp=2025-12-23T15:30:45 level=INFO module=analyzer msg=Started
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured key-value pairs."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        parts = [
            f"timestamp={timestamp}",
            f"level={record.levelname}",
            f"module={record.module}",
            f"func={record.funcName}",
            f"line={record.lineno}",
            f"msg={record.getMessage()}",
        ]
        
        # Add exception info if present
        if record.exc_info:
            parts.append(f"exception={record.exc_text}")
        
        return " ".join(parts)


# ============ LOGGER SETUP ============


class LoggerConfig:
    """
    Centralized logger configuration and setup.

    Manages logger creation, handlers, and formatting.
    """

    _logger_instance: Optional[logging.Logger] = None
    _configured: bool = False

    @staticmethod
    def configure(
        name: str = "signal_analyzer",
        level: LogLevel = "INFO",
        log_file: Optional[str] = None,
        format_style: Literal["detailed", "simple", "structured"] = "detailed",
        console_output: bool = True,
    ) -> logging.Logger:
        """
        Configure and return the logger instance.

        Sets up both console and optional file logging with the specified
        format and log level.

        Args:
            name: Logger name (used in log messages).
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            log_file: Optional path to log file. If provided, logs are written
                to file in addition to console.
            format_style: Style of log formatting (detailed, simple, structured).
            console_output: Whether to log to console (default: True).

        Returns:
            Configured logger instance.

        Example:
            >>> logger = LoggerConfig.configure(
            ...     level="DEBUG",
            ...     log_file="logs/analyzer.log"
            ... )
            >>> logger.info("Analysis started")
        """
        logger = logging.getLogger(name)
        
        # Only configure once
        if LoggerConfig._configured:
            return logger
        
        # Set log level
        logger.setLevel(getattr(logging, level))
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Select formatter
        if format_style == "structured":
            formatter = StructuredFormatter()
        elif format_style == "simple":
            formatter = SimpleFormatter()
        else:  # detailed
            formatter = DetailedFormatter()
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, level))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        LoggerConfig._configured = True
        LoggerConfig._logger_instance = logger
        
        return logger

    @staticmethod
    def get_logger(name: str = "signal_analyzer") -> logging.Logger:
        """
        Get the configured logger instance.

        If not yet configured, returns a basic logger without configuration.

        Args:
            name: Logger name.

        Returns:
            Logger instance (configured or basic).
        """
        if LoggerConfig._logger_instance is None:
            LoggerConfig._logger_instance = logging.getLogger(name)
        return LoggerConfig._logger_instance

    @staticmethod
    def reset() -> None:
        """Reset logger configuration (useful for testing)."""
        if LoggerConfig._logger_instance:
            LoggerConfig._logger_instance.handlers.clear()
        LoggerConfig._logger_instance = None
        LoggerConfig._configured = False


# ============ CONVENIENCE FUNCTION ============


def get_logger(name: str = "signal_analyzer") -> logging.Logger:
    """
    Get a configured logger instance.

    Convenience function that calls LoggerConfig.get_logger().

    Args:
        name: Logger name (default: "signal_analyzer").

    Returns:
        Logger instance.

    Example:
        >>> from logging_config import get_logger
        >>> logger = get_logger()
        >>> logger.info("Starting analysis")
    """
    return LoggerConfig.get_logger(name)


# ============ MODULE LOGGER ============

# Create module-level logger for use in this module
logger = logging.getLogger("signal_analyzer")


# ============ CONVENIENCE LOGGING FUNCTIONS ============


def log_analysis_start(symbol: str, interval: str, period: str) -> None:
    """
    Log the start of an analysis.

    Args:
        symbol: Stock symbol being analyzed.
        interval: Timeframe being analyzed.
        period: Data period being fetched.
    """
    logger.info(
        f"Starting analysis: symbol={symbol} interval={interval} period={period}"
    )


def log_data_fetched(symbol: str, bars_count: int, date_start: str, date_end: str) -> None:
    """
    Log successful data fetch.

    Args:
        symbol: Stock symbol.
        bars_count: Number of bars fetched.
        date_start: Start date of data.
        date_end: End date of data.
    """
    logger.info(
        f"Data fetched: symbol={symbol} bars={bars_count} "
        f"period={date_start} to {date_end}"
    )


def log_indicators_calculated(indicator_count: int) -> None:
    """
    Log successful indicator calculation.

    Args:
        indicator_count: Number of indicators calculated.
    """
    logger.info(f"Indicators calculated: count={indicator_count}")


def log_signals_detected(signal_count: int, bullish: int, bearish: int, neutral: int) -> None:
    """
    Log signal detection results.

    Args:
        signal_count: Total signals detected.
        bullish: Count of bullish signals.
        bearish: Count of bearish signals.
        neutral: Count of neutral signals.
    """
    logger.info(
        f"Signals detected: total={signal_count} "
        f"bullish={bullish} bearish={bearish} neutral={neutral}"
    )


def log_export_complete(export_format: str, filepath: str) -> None:
    """
    Log successful export.

    Args:
        export_format: Format of export (json, csv, markdown).
        filepath: Path where file was written.
    """
    logger.info(f"Export complete: format={export_format} path={filepath}")


def log_error_with_context(
    error: Exception,
    context: str,
    **kwargs: str,
) -> None:
    """
    Log an error with contextual information.

    Args:
        error: The exception that occurred.
        context: Contextual description of where error occurred.
        **kwargs: Additional context key-value pairs.
    """
    context_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error(
        f"Error in {context}: {type(error).__name__}: {str(error)} | {context_str}",
        exc_info=True,
    )