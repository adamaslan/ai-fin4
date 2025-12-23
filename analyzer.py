"""
Analysis pipeline.

Defines the complete analysis workflow with middleware-like composition.
Each step can be skipped or customized.
"""

from __future__ import annotations

from typing import Optional, Callable, List, Any
from dataclasses import dataclass
import pandas as pd
from logging_config import get_logger
from analyzer.core import MultiTimeframeAnalyzer, AnalysisResult
from config import SignalConfig
from data.provider import DataProvider, YFinanceProvider
from exceptions import AnalyzerError

logger = get_logger()


# ============ PIPELINE STEP RESULT ============


@dataclass
class StepResult:
    """Result from a pipeline step."""

    name: str
    """Step name."""

    success: bool
    """Whether step succeeded."""

    data: Any
    """Step output data."""

    error: Optional[str] = None
    """Error message if failed."""

    duration_ms: float = 0.0
    """Step execution time in milliseconds."""

    message: str = ""
    """Additional message."""

    def __str__(self) -> str:
        """Return formatted result."""
        status = "✓" if self.success else "✗"
        return f"{status} {self.name} ({self.duration_ms:.0f}ms)"


# ============ ANALYSIS PIPELINE ============


class AnalysisPipeline:
    """
    Complete market analysis pipeline.

    Composes analysis steps into a workflow:
    1. Fetch data
    2. Validate data
    3. Calculate indicators
    4. Detect signals
    5. Filter signals
    6. Export results

    Each step can be customized, skipped, or wrapped with middleware.

    Example:
        >>> pipeline = AnalysisPipeline(
        ...     symbol='SPY',
        ...     interval='1h',
        ... )
        >>> result = pipeline.run()
        >>> print(result.summary)
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
        skip_indicators: bool = False,
        skip_signals: bool = False,
        enable_progress: bool = True,
    ):
        """
        Initialize analysis pipeline.

        Args:
            symbol: Stock symbol.
            interval: Timeframe (default: '1d').
            period: Data period (default: auto).
            config: Custom SignalConfig.
            data_provider: Custom data provider.
            indicator_factory: Indicator suite name.
            detector_factory: Detector suite name.
            quality_min: Minimum signal quality.
            skip_indicators: Skip indicator calculation.
            skip_signals: Skip signal detection.
            enable_progress: Show progress during execution.
        """
        self.symbol = symbol
        self.interval = interval
        self.enable_progress = enable_progress

        # Create analyzer with all options
        self.analyzer = MultiTimeframeAnalyzer(
            symbol=symbol,
            interval=interval,
            period=period,
            config=config,
            data_provider=data_provider or YFinanceProvider(),
            indicator_factory=indicator_factory,
            detector_factory=detector_factory,
            quality_min=quality_min,
        )

        self.skip_indicators = skip_indicators
        self.skip_signals = skip_signals

        # Execution history
        self.steps: List[StepResult] = []

    def run(self) -> AnalysisResult:
        """
        Execute complete analysis pipeline.

        Returns:
            AnalysisResult with all analysis data.

        Raises:
            AnalyzerError: If any step fails (unless configured to continue).
        """
        logger.info(f"Starting analysis pipeline: {self.symbol} [{self.interval}]")

        try:
            # Step 1: Fetch data
            self._step_fetch_data()

            # Step 2: Calculate indicators (optional)
            if not self.skip_indicators:
                self._step_calculate_indicators()

            # Step 3: Detect signals (optional)
            if not self.skip_signals:
                self._step_detect_signals()

            # Complete
            result = self.analyzer.result
            if result is None:
                raise AnalyzerError("No result generated")

            self._log_summary(result)
            return result

        except AnalyzerError:
            raise
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise AnalyzerError(f"Pipeline error: {str(e)}") from e

    def _step_fetch_data(self) -> StepResult:
        """Execute fetch data step."""
        import time

        step_name = "Fetch Data"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            data = self.analyzer.fetch_data()

            result = StepResult(
                name=step_name,
                success=True,
                data=data,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{len(data)} bars fetched",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _step_calculate_indicators(self) -> StepResult:
        """Execute indicator calculation step."""
        import time

        step_name = "Calculate Indicators"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            data = self.analyzer.calculate_indicators()

            result = StepResult(
                name=step_name,
                success=True,
                data=data,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{len(data.columns)} columns (including indicators)",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _step_detect_signals(self) -> StepResult:
        """Execute signal detection step."""
        import time

        step_name = "Detect Signals"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            signal_result = self.analyzer.detect_signals()

            result = StepResult(
                name=step_name,
                success=True,
                data=signal_result,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{signal_result.signal_count} signals detected",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _log_step_start(self, step_name: str) -> None:
        """Log step start."""
        if self.enable_progress:
            logger.info(f"→ {step_name}...")

    def _log_step_result(self, result: StepResult) -> None:
        """Log step result."""
        if self.enable_progress:
            logger.info(f"  {result}")

    def _log_summary(self, result: AnalysisResult) -> None:
        """Log pipeline summary."""
        logger.info(f"Pipeline complete: {result}")
        logger.info("Steps:")
        for step in self.steps:
            status = "✓" if step.success else "✗"
            logger.info(f"  {status} {step.name} ({step.duration_ms:.0f}ms)")

    def get_summary(self) -> dict:
        """
        Get pipeline execution summary.

        Returns:
            Dictionary with execution stats.
        """
        successful = sum(1 for s in self.steps if s.success)
        total_time = sum(s.duration_ms for s in self.steps)

        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "steps_total": len(self.steps),
            "steps_successful": successful,
            "steps_failed": len(self.steps) - successful,
            "total_time_ms": total_time,
            "steps": [
                {
                    "name": s.name,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }

    def __str__(self) -> str:
        """Return string representation."""
        return f"AnalysisPipeline({self.symbol}[{self.interval}])"


# ============ CONVENIENCE FUNCTIONS ============


def analyze_symbol(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None,
    show_progress: bool = True,
) -> AnalysisResult:
    """
    Quick analysis of a symbol.

    Args:
        symbol: Stock symbol.
        interval: Timeframe (default: '1d').
        period: Data period (default: auto).
        show_progress: Show progress output.

    Returns:
        AnalysisResult with all analysis.

    Example:
        >>> result = analyze_symbol('SPY', interval='1h')
        >>> print(result.summary)
    """
    pipeline = AnalysisPipeline(
        symbol=symbol,
        interval=interval,
        period=period,
        enable_progress=show_progress,
    )
    return pipeline.run()


def analyze_multiple(
    symbols: List[str],
    interval: str = "1d",
    show_progress: bool = True,
) -> dict:
    """
    Analyze multiple symbols.

    Args:
        symbols: List of stock symbols.
        interval: Timeframe for all (default: '1d').
        show_progress: Show progress output.

    Returns:
        Dictionary mapping symbol to AnalysisResult.

    Example:
        >>> results = analyze_multiple(['SPY', 'QQQ', 'IWM'])
        >>> for symbol, result in results.items():
        ...     print(f"{symbol}: {result.signals.signal_count} signals")
    """
    results = {}

    for symbol in symbols:
        try:
            logger.info(f"Analyzing {symbol}...")
            results[symbol] = analyze_symbol(symbol, interval, show_progress=show_progress)
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {str(e)}")
            results[symbol] = None

    return results